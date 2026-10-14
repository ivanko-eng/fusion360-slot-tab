import adsk.core
import adsk.fusion

from ...lib import fusionAddInUtils as futil

def tab_edge_pre_select(args: adsk.core.SelectionEventArgs):
    # Command input (box) that is currently trying to receive a selection
    active_input = args.activeInput

    # Checks if the tab edge is the active input 
    if not active_input or active_input.id != 'tabEdge':
        return

    # Get the selected entity
    entity = args.selection.entity
    # Check if the selected entity is a BRepEdge
    edge = adsk.fusion.BRepEdge.cast(entity)

    if not edge:
        args.isSelectable = False
        return

    if not get_native_edge(edge).body.isSheetMetal:
        args.isSelectable = False
        return
    
    if are_faces_tangent_at_edge(edge):
        args.isSelectable = False
        return

    all_inputs = active_input.commandInputs

    advanced_edge_filter = adsk.core.BoolValueCommandInput.cast(all_inputs.itemById('advancedEdgeFilter'))

    if advanced_edge_filter and advanced_edge_filter.value:
        if is_straight_edge(edge) and is_of_thickness_length(edge):
            args.isSelectable = False
            return

def get_native_edge(edge: adsk.fusion.BRepEdge):
    if edge.nativeObject:
        return edge.nativeObject
    
    return edge

# def get_edge_body(edge: adsk.fusion.BRepEdge):
#     native_edge = get_native_edge(edge)
#     return native_edge.body

def get_edge_component(edge: adsk.fusion.BRepEdge):
    native_edge = get_native_edge(edge)
    return native_edge.body.parentComponent

def are_faces_tangent_at_edge(edge: adsk.fusion.BRepEdge):
    if edge.faces.count != 2:
        return False

    face_a = edge.faces.item(0)
    face_b = edge.faces.item(1)

    normal_a = face_a.evaluator.getNormalAtPoint(edge.startVertex.geometry)
    normal_b = face_b.evaluator.getNormalAtPoint(edge.startVertex.geometry)

    # Check if the normals are parallel (tangent)
    if normal_a[1].isParallelTo(normal_b[1]):
        return True

    return False

def is_straight_edge(edge: adsk.fusion.BRepEdge):
    # Check if the edge is a straight line
    return edge.geometry.curveType == adsk.core.Curve3DTypes.Line3DCurveType

def is_of_thickness_length(edge: adsk.fusion.BRepEdge):
    thickness = get_sheet_thickness(edge)

    if thickness is None:
        return None
    
    tolerance = 1e-4

    # Check if the edge length is approximately equal to the specified thickness
    return abs(edge.length - thickness) <= tolerance

def get_sheet_thickness(edge: adsk.fusion.BRepEdge):
    component = get_edge_component(edge)

    rule = component.activeSheetMetalRule

    if not rule:
        return None

    return rule.thickness.value