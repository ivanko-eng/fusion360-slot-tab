import adsk.core
import adsk.fusion

from ...lib import fusionAddInUtils as futil

from . import tab_edge_selection

def get_adjacent_thickness_face(edge: adsk.fusion.BRepEdge):
    faces = edge.faces
    
    for face in faces:

        # if face.edges.count != 4:
        #     continue

        thickness_edges = []

        for face_edge in face.edges:

            if not tab_edge_selection.is_straight_edge(face_edge):
                continue

            if  not tab_edge_selection.is_of_thickness_length(face_edge):
                continue

            thickness_edges.append(face_edge)

        if (
            len(thickness_edges) == 2
            and are_opposite_parallel_edges(
                thickness_edges[0],
                thickness_edges[1]
            )
        ):
            return face, thickness_edges
    
    return None, None

def are_opposite_parallel_edges(
    edge_a: adsk.fusion.BRepEdge, 
    edge_b: adsk.fusion.BRepEdge
):
    a_start = edge_a.startVertex
    a_end = edge_a.endVertex

    b_start = edge_b.startVertex
    b_end = edge_b.endVertex

    direction_a = a_start.geometry.vectorTo(a_end.geometry)
    direction_b = b_start.geometry.vectorTo(b_end.geometry)

    if not direction_a.isParallelTo(direction_b):
        return False
    
    if (
        a_start == b_start or 
        a_start == b_end or 
        a_end == b_start or 
        a_end == b_end
    ):
        return False

    return True