# -*- coding: utf-8 -*-

import FreeCAD
import Part
import Sketcher


def drawFrame(sketch, width, height):
    p_vec = FreeCAD.Vector(width / -2, height / 2, 0)

    pnt_1 = Part.Point(p_vec)
    sketch.addGeometry(pnt_1, False)
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

    return pnt_1
