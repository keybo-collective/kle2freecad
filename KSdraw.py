# -*- coding: utf-8 -*-

import FreeCAD
import Part
import Sketcher
import math
from kle_json_cleaner import countCols, countRows, countKeys


# ............................................................................

def drawRect(sketch, x, y, w, h, r, k):
    """Draws a rectangle"""

    if sketch is None:
        return False

    lft = x - (w / 2)
    rte = x + (w / 2)
    top = y + (h / 2)
    btm = y - (h / 2)

    # TODO : account for `kerf`

    # Batch geometry/constraints to reduce per-call overhead when creating many keys.
    if r > 0:
        z = max(w, h) / 2
        if r > z:
            r = z;

        i_lft = lft + r
        i_rte = rte - r
        i_top = top - r
        i_btm = btm + r

        geoms = [
            Part.LineSegment(FreeCAD.Vector(i_lft, top, 0), FreeCAD.Vector(i_rte, top, 0)),
            Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(i_rte, i_top, 0), FreeCAD.Vector(0, 0, 1), r), 0.0, 1.5708),
            Part.LineSegment(FreeCAD.Vector(rte, i_top, 0), FreeCAD.Vector(rte, i_btm, 0)),
            Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(i_rte, i_btm, 0), FreeCAD.Vector(0, 0, 1), r), 4.7124, 6.28319),
            Part.LineSegment(FreeCAD.Vector(i_rte, btm, 0), FreeCAD.Vector(i_lft, btm, 0)),
            Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(i_lft, i_btm, 0), FreeCAD.Vector(0, 0, 1), r), 3.1416, 4.7124),
            Part.LineSegment(FreeCAD.Vector(lft, i_btm, 0), FreeCAD.Vector(lft, i_top, 0)),
            Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(i_lft, i_top, 0), FreeCAD.Vector(0, 0, 1), r), 1.5708, 3.1416),
        ]
    else:
        geoms = [
            Part.LineSegment(FreeCAD.Vector(lft, top, 0), FreeCAD.Vector(rte, top, 0)),
            Part.LineSegment(FreeCAD.Vector(rte, top, 0), FreeCAD.Vector(rte, btm, 0)),
            Part.LineSegment(FreeCAD.Vector(rte, btm, 0), FreeCAD.Vector(lft, btm, 0)),
            Part.LineSegment(FreeCAD.Vector(lft, btm, 0), FreeCAD.Vector(lft, top, 0)),
        ]
    geom_indices = sketch.addGeometry(geoms, False)

    if r > 0:
        constraints = [
            Sketcher.Constraint('Coincident', geom_indices[0], 2, geom_indices[1], 2),
            Sketcher.Constraint('Coincident', geom_indices[1], 1, geom_indices[2], 1),
            Sketcher.Constraint('Coincident', geom_indices[2], 2, geom_indices[3], 2),
            Sketcher.Constraint('Coincident', geom_indices[3], 1, geom_indices[4], 1),
            Sketcher.Constraint('Coincident', geom_indices[4], 2, geom_indices[5], 2),
            Sketcher.Constraint('Coincident', geom_indices[5], 1, geom_indices[6], 1),
            Sketcher.Constraint('Coincident', geom_indices[6], 2, geom_indices[7], 2),
            Sketcher.Constraint('Coincident', geom_indices[7], 1, geom_indices[0], 1),
        ]
    else:
        constraints = [
            Sketcher.Constraint('Coincident', geom_indices[0], 2, geom_indices[1], 1),
            Sketcher.Constraint('Coincident', geom_indices[1], 2, geom_indices[2], 1),
            Sketcher.Constraint('Coincident', geom_indices[2], 2, geom_indices[3], 1),
            Sketcher.Constraint('Coincident', geom_indices[3], 2, geom_indices[0], 1),
        ]
    constraints.extend(Sketcher.Constraint('Block', idx) for idx in geom_indices)
    sketch.addConstraint(constraints)

    return True # Success

# ----------------------------------------------------------------------------

def drawFrame(sketch, width, height):
    p_vec = FreeCAD.Vector(width / -2, height / 2, 0)

    home_p = Part.Point(p_vec)
    home_i = sketch.addGeometry(home_p, True)
    dx_idx = sketch.addConstraint(Sketcher.Constraint('DistanceX', -1, 1, 0, 1, width))
    dy_idx = sketch.addConstraint(Sketcher.Constraint('DistanceY', -1, 1, 0, 1, height))
    sketch.setDatum(dx_idx, FreeCAD.Units.Quantity(f"{(width / -2):.6f} mm"))
    sketch.setDatum(dy_idx, FreeCAD.Units.Quantity(f"{(height / 2):.6f} mm"))

    ln1 = Part.LineSegment(p_vec, FreeCAD.Vector(p_vec.x + width, p_vec.y, 0))
    ln1_idx = sketch.addGeometry(ln1, False)
    sketch.addConstraint(Sketcher.Constraint('Coincident', ln1_idx, 1, 0, 1))
    sketch.addConstraint(Sketcher.Constraint('Horizontal', ln1_idx))
    len1_idx = sketch.addConstraint(Sketcher.Constraint('DistanceX', ln1_idx, 1, ln1_idx, 2, width))
    sketch.setDatum(len1_idx, FreeCAD.Units.Quantity(f"{width:.6f} mm"))

    ln2 = Part.LineSegment(FreeCAD.Vector(width / 2, height / 2, 0), FreeCAD.Vector(width / 2, height / -2, 0))
    ln2_idx = sketch.addGeometry(ln2, False)
    len2_idx = sketch.addConstraint(Sketcher.Constraint('DistanceY', ln2_idx, 2, ln2_idx, 1, height))
    sketch.setDatum(len2_idx, FreeCAD.Units.Quantity(f"{height:.6f} mm"))
    sketch.addConstraint(Sketcher.Constraint('Coincident', ln2_idx, 1, ln1_idx, 2))
    sketch.addConstraint(Sketcher.Constraint('Perpendicular', ln1_idx, ln2_idx))

    ln3 = Part.LineSegment(FreeCAD.Vector(width / 2, height / -2, 0), FreeCAD.Vector(width / -2, height / -2, 0))
    ln3_idx = sketch.addGeometry(ln3, False)
    sketch.addConstraint(Sketcher.Constraint('Coincident', ln3_idx, 1, ln2_idx, 2))
    sketch.addConstraint(Sketcher.Constraint('Parallel', ln3_idx, ln1_idx))

    ln4 = Part.LineSegment(FreeCAD.Vector(width / -2, height / -2, 0), FreeCAD.Vector(width / -2, height / 2, 0))
    ln4_idx = sketch.addGeometry(ln4, False)
    sketch.addConstraint(Sketcher.Constraint('Coincident', ln4_idx, 1, ln3_idx, 2))
    sketch.addConstraint(Sketcher.Constraint('Coincident', ln4_idx, 2, ln1_idx, 1))
    sketch.addConstraint(Sketcher.Constraint('Parallel', ln4_idx, ln2_idx))

    return home_i

# ----------------------------------------------------------------------------

def findKeyCenters(kle_clean, m_w, m_h):
    """loop over a clean key array and insert the center coordinates as c:e"""

    if not kle_clean:
        return False

    h_w = countCols(kle_clean) / -2
    h_h = countRows(kle_clean) / 2

    for row in kle_clean:
        if not isinstance(row, list):
            continue
        for item in row:
            if isinstance(item, dict):
                item["cx"] = (h_w + (item.get("x",0) + (item.get("w",1)/2))) * m_w
                item["cy"] = (h_h - (item.get("y",0) + (item.get("h",1)/2))) * m_h

    return kle_clean

# ----------------------------------------------------------------------------

def drawCenter(sketch, cx, cy):
    """Render draft point representing the center"""

    if sketch is None:
        return False

    i = sketch.addGeometry(Part.Point(FreeCAD.Vector(cx, cy, 0)), True)
    sketch.addConstraint(Sketcher.Constraint('Block', i))

    return True

# ----------------------------------------------------------------------------

def drawCherryKey(sketch, cx, cy, flt_r, kerf):
    """Draws a 14x14 plate cutout"""

    z = 14
    return drawRect(sketch, cx, cy, z, z, flt_r, kerf)

# ----------------------------------------------------------------------------

def drawCherryStab(sketch, cx, cy, width, height, angle, flt_r, kerf):
    """Draws a plate stab cutout"""

    o_r = int(((angle % 360) / 90.0) + 0.5) % 4
    z = max(width, height)
    if z >= 7:
        o_o = 57.15
    elif z >= 6.25:
        o_o = 50.0
    elif z >= 6:
        o_o = 47.63
    elif z >= 3:
        o_o = 19.05
    elif z >= 2:
        o_o = 11.94
    else:
        o_o = 0

    if (o_r & 1) == 0:
        x1 = cx - o_o
        x2 = cx + o_o
        y1 = y2 = cy + (-1.5 if o_r == 0 else 1.5)
        w = 7
        h = 15
    else:
        x1 = x2 = cx + (-1.5 if o_r == 1 else 1.5)
        y1 = cy - o_o
        y2 = cy + o_o
        w = 15
        h = 7

    return drawRect(sketch, x1, y1, w, h, flt_r, kerf) & drawRect(sketch, x2, y2, w, h, flt_r, kerf)
