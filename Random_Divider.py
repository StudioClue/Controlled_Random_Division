# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import scriptcontext as sc
import System.Drawing.Color as Color
import random

# === SETTINGS ===
panelSizes = [12, 15, 18, 24, 30, 36]
max_loops = 150
extrude_height = 30
min_step = 1e-6
delete_circles = True
circle_color_range = (80, 255)

# === SELECT CURVE ===
crv = rs.GetObject("Select a base curve", rs.filter.curve)
if not crv:
    print("No curve selected.")
    exit()

previous_layer = rs.CurrentLayer()
startPt = rs.CurveStartPoint(crv)
firstPt = startPt
t_current = rs.CurveClosestPoint(crv, startPt)
if t_current is None:
    print("Couldn't find start parameter.")
    exit()

# === STORAGE ===
int_Pt = [startPt]
Radius = []
circles = []
lines = []
extrusions = []

# === UTILITY FUNCTIONS ===

def random_color():
    r1, r2 = circle_color_range
    return Color.FromArgb(random.randint(r1, r2), random.randint(r1, r2), random.randint(r1, r2))

def ensure_layer(name):
    """Creates a new layer with a random color if it doesn't exist."""
    if not rs.IsLayer(name):
        rs.AddLayer(name, random_color())
    return name

def create_extrusion(line, layer_name):
    """Extrudes a curve vertically and assigns it to a specified layer."""
    ensure_layer(layer_name)
    rs.CurrentLayer(layer_name)
    vec = rs.VectorCreate([0, 0, extrude_height], [0, 0, 0])
    ext = rs.ExtrudeCurveStraight(line, [0, 0, 0], vec)
    if ext:
        rs.ObjectLayer(ext, layer_name)
        extrusions.append(ext)

# === MAIN LOOP ===

for i in range(max_loops):
    radius = random.choice(panelSizes)
    Radius.append(radius)

    circle = rs.AddCircle(startPt, radius)
    circles.append(circle)

    inters = rs.CurveCurveIntersection(crv, circle)
    if not inters:
        break

    forward_candidates = []
    all_pts = []

    for result in inters:
        pt = result[1]
        t_pt = rs.CurveClosestPoint(crv, pt)
        if t_pt is not None:
            all_pts.append((t_pt, pt))
            if t_pt > t_current + min_step:
                forward_candidates.append((t_pt, pt))

    if forward_candidates:
        t_next, pt_next = sorted(forward_candidates, key=lambda x: x[0])[0]
    elif all_pts:
        fallback = [p for p in all_pts if p[0] > t_current - 0.05]
        if fallback:
            t_next, pt_next = sorted(fallback, key=lambda x: rs.Distance(startPt, x[1]), reverse=True)[0]
        else:
            break
    else:
        break

    if rs.Distance(startPt, pt_next) < radius * 0.25 or abs(t_next - t_current) < 1e-4:
        break

    # Add Line + Layer
    line = rs.AddLine(startPt, pt_next)
    lines.append(line)

    line_layer = "line_{}".format(int(radius))
    ensure_layer(line_layer)
    rs.ObjectLayer(line, line_layer)

    # Add Extrusion
    create_extrusion(line, "ext_{}".format(int(radius)))

    # Advance
    startPt = pt_next
    t_current = t_next
    int_Pt.append(pt_next)

# === FINAL CLOSURE PANEL ===
if len(int_Pt) >= 2:
    lastPt = int_Pt[-1]
    if rs.Distance(lastPt, firstPt) > 1e-2:
        ensure_layer("last")
        line = rs.AddLine(lastPt, firstPt)
        lines.append(line)
        rs.ObjectLayer(line, "last")
        create_extrusion(line, "last")

# === CLEANUP ===
rs.CurrentLayer(previous_layer)
if delete_circles:
    rs.DeleteObjects(circles)

# === REPORT ===
print("✅ Done. {} lines and {} extrusions created.".format(len(lines), len(extrusions)))
print("Used panel sizes: {}".format(sorted(set(int(r) for r in Radius))))
