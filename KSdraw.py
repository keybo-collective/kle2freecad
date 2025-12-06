# -*- coding: utf-8 -*-

import FreeCAD
import Part
import Sketcher
import math
from kle_json_cleaner import countCols, countRows
from KSutils import debug_print_tree

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

def drawAndGetKeyCenters(sketch, kle_clean, m_w, m_h):
    """Render draft point representing the center of each key & return a list of Geometry indices"""

    if sketch is None:
        return False

    if not kle_clean:
        return False

    h_w = countCols(kle_clean) / -2
    h_h = countRows(kle_clean) / 2
    # print(h_w, h_h); # FIXME : debug

    geom_indices = []

    for row in kle_clean:
        if not isinstance(row, list):
            continue
        for item in row:
            if isinstance(item, dict):
                x = item.get("x")
                y = item.get("y")
                w = item.get("w")
                h = item.get("h")
                # r = item.get("r", 0)

                v_x = (h_w + (x + (w/2))) * m_w
                v_y = (h_h - (y + (h/2))) * m_h

                i = sketch.addGeometry(Part.Point(FreeCAD.Vector(v_x, v_y, 0)), True)
                j = sketch.addConstraint(Sketcher.Constraint('DistanceX', i, 1, -1, 1, v_x))
                sketch.setDatum(j, FreeCAD.Units.Quantity(f"{v_x:.6f} mm"))
                j = sketch.addConstraint(Sketcher.Constraint('DistanceY', i, 1, -1, 1, v_y))
                sketch.setDatum(j, FreeCAD.Units.Quantity(f"{v_y:.6f} mm"))

                geom_indices.append(i)

    return geom_indices

# ----------------------------------------------------------------------------

def drawCherryKey(sketch, home_pnt_idx, flt_r, kerf):
    """Draws a 14x14 plate cutout"""

    if sketch is None:
        return False

    if home_pnt_idx < 0:
        return False

    home_pnt = sketch.Geometry[home_pnt_idx]
    z = 14

    lft = home_pnt.X - (z / 2)
    rte = home_pnt.X + (z / 2)
    top = home_pnt.Y + (z / 2)
    btm = home_pnt.Y - (z / 2)
    if flt_r > z * 0.5:
        flt_r = 0

    # TODO : account for `kerf`

    i_lft = lft + flt_r
    i_rte = rte - flt_r
    i_top = top - flt_r
    i_btm = btm + flt_r

    print(home_pnt, home_pnt.X, home_pnt.Y, lft, rte, top, btm, i_lft, i_rte, i_top, i_btm)

    # return True # FIXME : debug

    geom_indices = []

    # [0] top edge
    geom_indices.append(sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(i_lft, top, 0), FreeCAD.Vector(i_rte, top, 0)), False))
    # sketch.addConstraint(Sketcher.Constraint('Horizontal', geom_indices[0]))
    # i = sketch.addConstraint(Sketcher.Constraint('DistanceX', home_pnt_idx, 1, geom_indices[0], 1, i_lft))
    # sketch.setDatum(i, FreeCAD.Units.Quantity(f"{i_lft:.6f} mm"))
    # i = sketch.addConstraint(Sketcher.Constraint('DistanceY', home_pnt_idx, 1, geom_indices[0], 1, top))
    # sketch.setDatum(i, FreeCAD.Units.Quantity(f"{top:.6f} mm"))
    # i = sketch.addConstraint(Sketcher.Constraint('Distance', geom_indices[0], 1, geom_indices[0], 2, (i_rte - i_lft)))
    # sketch.setDatum(i, FreeCAD.Units.Quantity(f"{(i_rte - i_lft):.6f} mm"))

    # [1] draft
    geom_indices.append(sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(i_rte, top, 0), FreeCAD.Vector(i_rte, i_top, 0)), True))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[0], 2, geom_indices[1], 1))
    # sketch.addConstraint(Sketcher.Constraint('Perpendicular', geom_indices[0], geom_indices[1]))
    # i = sketch.addConstraint(Sketcher.Constraint('Distance', geom_indices[1], 1, geom_indices[1], 2, flt_r))
    # sketch.setDatum(i, FreeCAD.Units.Quantity(f"{flt_r:.6f} mm"))

    # [2] draft
    geom_indices.append(sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(i_rte, i_top, 0), FreeCAD.Vector(rte, i_top, 0)), True))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[1], 2, geom_indices[2], 1))
    # sketch.addConstraint(Sketcher.Constraint('Perpendicular', geom_indices[1], geom_indices[2]))

    # [3] top right arc
    geom_indices.append(sketch.addGeometry(Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(i_rte, i_top, 0), FreeCAD.Vector(0, 0, 1), flt_r), 0.0, 1.5708)))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[2], 1, geom_indices[3], 3))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[2], 2, geom_indices[3], 1))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[1], 1, geom_indices[3], 2))

    # [4] right edge
    geom_indices.append(sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(rte, i_top, 0), FreeCAD.Vector(rte, i_btm, 0)), False))
    # sketch.addConstraint(Sketcher.Constraint('Vertical', geom_indices[4]))
    # i = sketch.addConstraint(Sketcher.Constraint('Distance', geom_indices[4], 1, geom_indices[4], 2, (i_top - i_btm)))
    # sketch.setDatum(i, FreeCAD.Units.Quantity(f"{(i_top - i_btm):.6f} mm"))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[3], 1, geom_indices[4], 1))

    # [5] draft
    geom_indices.append(sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(rte, i_btm, 0), FreeCAD.Vector(i_rte, i_btm, 0)), True))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[4], 2, geom_indices[5], 1))
    # sketch.addConstraint(Sketcher.Constraint('Perpendicular', geom_indices[4], geom_indices[5]))
    # i = sketch.addConstraint(Sketcher.Constraint('Distance', geom_indices[5], 1, geom_indices[5], 2, flt_r))
    # sketch.setDatum(i, FreeCAD.Units.Quantity(f"{flt_r:.6f} mm"))

    # [6] draft
    geom_indices.append(sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(i_rte, i_btm, 0), FreeCAD.Vector(i_rte, btm, 0)), True))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[5], 2, geom_indices[6], 1))
    # sketch.addConstraint(Sketcher.Constraint('Perpendicular', geom_indices[5], geom_indices[6]))

    # [7] bottom right arc
    geom_indices.append(sketch.addGeometry(Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(i_rte, i_btm, 0), FreeCAD.Vector(0, 0, 1), flt_r), 4.7124, 6.28319)))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[6], 1, geom_indices[7], 3))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[5], 1, geom_indices[7], 2))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[6], 2, geom_indices[7], 1))

    # [8] bottom edge
    geom_indices.append(sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(i_rte, btm, 0), FreeCAD.Vector(i_lft, btm, 0)), False))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[7], 1, geom_indices[8], 1))
    # sketch.addConstraint(Sketcher.Constraint('Horizontal', geom_indices[8]))
    # sketch.addConstraint(Sketcher.Constraint('Equal', geom_indices[0], geom_indices[8]))

    # [9] draft
    geom_indices.append(sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(i_lft, btm, 0), FreeCAD.Vector(i_lft, i_btm, 0)), True))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[8], 2, geom_indices[9], 1))
    # sketch.addConstraint(Sketcher.Constraint('Perpendicular', geom_indices[8], geom_indices[9]))
    # sketch.addConstraint(Sketcher.Constraint('Equal', geom_indices[6], geom_indices[9]))

    # [10] draft
    geom_indices.append(sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(i_lft, i_btm, 0), FreeCAD.Vector(lft, i_btm, 0)), True))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[9], 2, geom_indices[10], 1))
    # sketch.addConstraint(Sketcher.Constraint('Perpendicular', geom_indices[9], geom_indices[10]))

    # [11] bottom left arc
    geom_indices.append(sketch.addGeometry(Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(i_lft, i_btm, 0), FreeCAD.Vector(0, 0, 1), flt_r), 3.1416, 4.7124)))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[10], 1, geom_indices[11], 3))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[9], 1, geom_indices[11], 2))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[10], 2, geom_indices[11], 1))

    # [12] left edge
    geom_indices.append(sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(lft, i_btm, 0), FreeCAD.Vector(lft, i_top, 0)), False))
    # sketch.addConstraint(Sketcher.Constraint('Vertical', geom_indices[12]))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[11], 1, geom_indices[12], 1))
    # sketch.addConstraint(Sketcher.Constraint('Equal', geom_indices[4], geom_indices[12]))

    # [13] draft
    geom_indices.append(sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(lft, i_top, 0), FreeCAD.Vector(i_lft, i_top, 0)), True))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[12], 2, geom_indices[13], 1))
    # sketch.addConstraint(Sketcher.Constraint('Perpendicular', geom_indices[12], geom_indices[13]))

    # [14] top left arc
    geom_indices.append(sketch.addGeometry(Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(i_lft, i_top, 0), FreeCAD.Vector(0, 0, 1), flt_r), 1.5708, 3.1416)))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[13], 2, geom_indices[14], 3))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[13], 1, geom_indices[14], 2))
    # sketch.addConstraint(Sketcher.Constraint('Coincident', geom_indices[14], 1, geom_indices[0], 1))

    del geom_indices

    return True # Success
