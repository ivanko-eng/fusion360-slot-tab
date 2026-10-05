import adsk.core
import adsk.fusion

from ...lib import fusionAddInUtils as futil

def tab_face_pre_select(args: adsk.core.SelectionEventArgs):
    # Command input (box) that is currently trying to receive a selection
    active_input = args.activeInput

    # Checks if the tab face is the active input
    if not active_input or active_input.id != 'tabFace':
        return

    # Get the selected entity
    entity = args.selection.entity
    # Check if the selected entity is a BRepFace
    face = adsk.fusion.BRepFace.cast(entity)

    if not face:
        args.isSelectable = False
        return

    native_face = get_native_face(face)

    if not native_face.body.isSheetMetal:
        args.isSelectable = False
        return

    all_inputs = active_input.commandInputs

    advanced_face_filter = adsk.core.BoolValueCommandInput.cast(all_inputs.itemById('advancedFilter'))

    if advanced_face_filter and advanced_face_filter.value:
        if not is_valid_tab_face(native_face):
            args.isSelectable = False
            return

def get_native_face(face: adsk.fusion.BRepFace):
    if face.nativeObject:
        #futil.log(f'Face is a proxy, native object: {face.nativeObject}')
        return face.nativeObject

    #futil.log(f'{face} is already a native face')
    return face

# def get_face_body(face: adsk.fusion.BRepFace):
#     native_face = get_native_face(face)
#     return native_face.body

def get_face_component(face: adsk.fusion.BRepFace):
    native_face = get_native_face(face)
    return native_face.body.parentComponent

def is_valid_tab_face(face: adsk.fusion.BRepFace):
    if face.edges.count != 4:
        return False

    thickness = get_sheet_thickness(face)

    if thickness is None:
        return False

    thickness_edges = []

    for edge in face.edges:

        if not is_straight_edge(edge):
            continue

        if is_of_thickness_length(edge, thickness):
            thickness_edges.append(edge)

    if len(thickness_edges) != 2:
        return False

    if not are_opposite_parallel_edges(thickness_edges[0], thickness_edges[1]):
        return False

    return True

def is_straight_edge(edge: adsk.fusion.BRepEdge):
    # Check if the edge is a straight line
    return edge.geometry.curveType == adsk.core.Curve3DTypes.Line3DCurveType

def get_sheet_thickness(face: adsk.fusion.BRepFace):
    component = get_face_component(face)

    rule = component.activeSheetMetalRule

    if not rule:
        return None

    return rule.thickness.value

def is_of_thickness_length(edge: adsk.fusion.BRepEdge, thickness: float):    
    tolerance = 1e-4

    # Check if the edge length is approximately equal to the specified thickness
    return abs(edge.length - thickness) <= tolerance

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