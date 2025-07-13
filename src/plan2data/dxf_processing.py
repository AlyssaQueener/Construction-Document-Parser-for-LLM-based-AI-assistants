import convert_pdf_to_dxf 
import ezdxf 
from ezdxf.math import Vec2
from collections import defaultdict

def convert_PDF_to_cm_point(PDF_scale=1,PDF_x, PDF_y):
    PDF_Unit_to_cm   =2.54/72 # 72 pdf UNits = 1 inch = 2,54 cm 
    CM_x= PDF_x*PDF_Unit_to_cm*PDF_scale
    CM_y =PDF_y*PDF_scale*PDF_scale
    Pt_cm = (CM_x,CM_y)
    return Pt_cm
def convert_PDF_to_cm(PDF_scale=1,PDF_cord):
    PDF_Unit_to_cm   =2.54/72 # 72 pdf UNits = 1 inch = 2,54 cm 
    CM_cord= PDF_cord*PDF_Unit_to_cm*PDF_scale
    return CM_cord

PROXIMITY_THRESHOLD = 1.0  # units depend on your PDF scale
# are the lines close? 
def is_close(p1, p2, tol=1.0):
    return (Vec2(p1) - Vec2(p2)).magnitude <= tol
# define a graph to group if the endpoints are within 
def build_line_graph(entities, tol=1.0):
    connections = defaultdict(list)
    lines = []

    for e in entities:
        if e.dxftype() == 'LINE':
            start = Vec2(e.dxf.start)
            end = Vec2(e.dxf.end)
            lines.append((start, end))
            connections[tuple(start)].append(tuple(end))
            connections[tuple(end)].append(tuple(start))

    return lines, connections