import adsk.core
import adsk.fusion

from ...lib import fusionAddInUtils as futil

def update_tab_parameters(inputs: adsk.core.CommandInputs):

    # Get inputs
    edge_input = adsk.core.SelectionCommandInput.cast(inputs.itemById('tabEdge'))

    reverse_direction_input = adsk.core.BoolValueCommandInput.cast(inputs.itemById('reverseDirection'))

    start_offset_input = adsk.core.ValueCommandInput.cast(inputs.itemById('startOffsetValue'))

    end_offset_input = adsk.core.ValueCommandInput.cast(inputs.itemById('endOffsetValue'))

    tab_count_input = adsk.core.IntegerSpinnerCommandInput.cast(inputs.itemById('tabCount'))

    mode_input = adsk.core.DropDownCommandInput.cast(inputs.itemById('distributionMode'))

    tab_width_input = adsk.core.ValueCommandInput.cast(inputs.itemById('tabWidth'))
    
    tab_gap_input = adsk.core.ValueCommandInput.cast(inputs.itemById('tabGap'))

    if edge_input.selectionCount == 0:
        futil.log('Error. No tab edge selected.')
        return

    edge = adsk.fusion.BRepEdge.cast(edge_input.selection(0).entity)

    tab_count = tab_count_input.value
    start_offset = start_offset_input.value

    if start_offset < 0:
        futil.log('Error. Start offset value must be non-negative.')
        return

    selected_mode = mode_input.selectedItem.name

    if selected_mode == 'Tab Width':
        tab_width = tab_width_input.value
        end_offset = end_offset_input.value

        available_length = get_available_length(edge, start_offset, end_offset)

        if available_length <= 0:
            futil.log(f'Error. No avaliable edge length after offsets applied.\nSelected edge length: {edge.length}')
            return

        gap = calculate_gap(available_length, tab_count, tab_width)

        if gap is None:
            futil.log('Invalid tab distribution: tabs exceed available length.')
            return
        
        tab_gap_input.value = gap

    elif selected_mode == 'Gap':
        gap = tab_gap_input.value
        end_offset = end_offset_input.value

        available_length = get_available_length(edge, start_offset, end_offset)
        
        if available_length <= 0:
            futil.log(f'Error. No avaliable edge length after offsets applied.\nSelected edge length: {edge.length}')
            return
                
        tab_width = calculate_tab_width(available_length, tab_count, gap)

        if tab_width is None:
            futil.log('Invalid tab distribution: tabs exceed available length.')
            return
        
        tab_width_input.value = tab_width

    elif selected_mode == "Tab Width & Gap":
        tab_width = tab_width_input.value
        gap = tab_gap_input.value

        end_offset = calculate_end_offset(edge.length, start_offset, tab_count, tab_width, gap)

        if end_offset is None:
            futil.log('Invalid tab distribution: tabs exceed available length.')
            return
        
        end_offset_input.value = end_offset

    positions = calculate_tab_positions(
        edge,
        start_offset_input.value,
        tab_count_input.value,
        tab_width_input.value,
        tab_gap_input.value,
        reverse_direction_input.value
    )

    for i, (start, end) in enumerate(positions, start=1):
        futil.log(
            f'Tab {i}: '
            f'Start ({start.x:.3f}, {start.y:.3f}, {start.z:.3f}) '
            f'End ({end.x:.3f}, {end.y:.3f}, {end.z:.3f})'
        )

def calculate_tab_positions(
    edge: adsk.fusion.BRepEdge,
    start_offset: float,
    tab_count: int,
    tab_width: float,
    gap: float,
    reverse_direction: bool = False
):
    ranges = calculate_tab_ranges(start_offset, tab_count, tab_width, gap)

    for start_distance, end_distance in ranges:
        if (
            start_distance < 0
            or end_distance > edge.length + 1e-7
            or end_distance <= start_distance
        ):
            futil.log(
                f'Invalid tab range: {start_distance:.4f} to {end_distance:.4f}. '
                f'\nEdge length: {edge.length:.4f}'
            )
            return []

    positions = []

    for start_distance, end_distance in ranges:

        start_point = get_point_at_distance(edge, start_distance, reverse_direction)
        end_point = get_point_at_distance(edge, end_distance, reverse_direction)

        positions.append((start_point, end_point))

    return positions

def calculate_tab_ranges(
    start_offset: float,
    tab_count: int,
    tab_width: float,
    gap: float
):
    ranges = []

    current_start = start_offset

    for _ in range(tab_count):

        current_end = current_start + tab_width

        ranges.append((current_start, current_end))

        current_start = current_end + gap

    return ranges

def get_point_at_distance(
    edge: adsk.fusion.BRepEdge,
    distance: float,
    reverse_direction: bool = False
) -> adsk.core.Point3D | None:

    evaluator = edge.evaluator

    success, start_param, end_param = evaluator.getParameterExtents()

    if not success:
        raise RuntimeError('Failed to get edge parameter extents.')

    edge_length = edge.length

    if distance < -1e-7 or distance > edge_length + 1e-7:
        raise ValueError(f'Tab position {distance:.4f} is outside edge length {edge_length:.4f}')

    if reverse_direction:
        distance = edge_length - distance

    success, parameter = evaluator.getParameterAtLength(start_param, distance)

    if not success:
        raise RuntimeError('Failed to calculate edge parameter.')

    if not start_param - 1e-7 <= parameter <= end_param + 1e-7:
        raise ValueError(f'Calculated parameter {parameter} is outside valid range [{start_param}, {end_param}]')
    
    success, point = evaluator.getPointAtParameter(parameter)

    if not success:
        raise RuntimeError('Failed to calculate point on edge.')

    return point

    # Get inputs
    edge_input = adsk.core.SelectionCommandInput.cast(inputs.itemById('tabEdge'))

    start_offset_input = adsk.core.ValueCommandInput.cast(inputs.itemById('startOffsetValue'))

    end_offset_input = adsk.core.ValueCommandInput.cast(inputs.itemById('endOffsetValue'))

    tab_count_input = adsk.core.IntegerSpinnerCommandInput.cast(inputs.itemById('tabCount'))

    mode_input = adsk.core.DropDownCommandInput.cast(inputs.itemById('distributionMode'))

    tab_width_input = adsk.core.ValueCommandInput.cast(inputs.itemById('tabWidth'))
    
    tab_gap_input = adsk.core.ValueCommandInput.cast(inputs.itemById('tabGap'))

    if edge_input.selectionCount == 0:
        futil.log('Error. No tab edge selected.')
        return

    edge = adsk.fusion.BRepEdge.cast(edge_input.selection(0).entity)

    tab_count = tab_count_input.value
    start_offset = start_offset_input.value

    if start_offset < 0:
        futil.log('Error. Start offset value must be non-negative.')
        return

    selected_mode = mode_input.selectedItem.name

    if selected_mode == 'Tab Width':
        tab_width = tab_width_input.value
        end_offset = end_offset_input.value

        available_length = get_available_length(edge, start_offset, end_offset)

        if available_length <= 0:
            futil.log(f'Error. No avaliable edge length after offsets applied.\nSelected edge length: {edge.length}')
            return

        gap = calculate_gap(available_length, tab_count, tab_width)

        if gap is None:
            futil.log('Invalid tab distribution: tabs exceed available length.')
            return
        
        tab_gap_input.value = gap

    elif selected_mode == 'Gap':
        gap = tab_gap_input.value
        end_offset = end_offset_input.value

        available_length = get_available_length(edge, start_offset, end_offset)
        
        if available_length <= 0:
            futil.log(f'Error. No avaliable edge length after offsets applied.\nSelected edge length: {edge.length}')
            return
                
        tab_width = calculate_tab_width(available_length, tab_count, gap)

        if tab_width is None:
            futil.log('Invalid tab distribution: tabs exceed available length.')
            return
        
        tab_width_input.value = tab_width

    elif selected_mode == "Tab Width & Gap":
        tab_width = tab_width_input.value
        gap = tab_gap_input.value

        end_offset = calculate_end_offset(edge.length, start_offset, tab_count, tab_width, gap)

        if end_offset is None:
            futil.log('Invalid tab distribution: tabs exceed available length.')
            return
        
        end_offset_input.value = end_offset

    positions = calculate_tab_positions(
        edge,
        start_offset_input.value,
        tab_count_input.value,
        tab_width_input.value,
        tab_gap_input.value
    )

    for i, (start, end) in enumerate(positions, start=1):
        futil.log(
            f'Tab {i}: '
            f'Start ({start.x:.3f}, {start.y:.3f}, {start.z:.3f}) '
            f'End ({end.x:.3f}, {end.y:.3f}, {end.z:.3f})'
        )

def get_available_length(
    edge: adsk.fusion.BRepEdge,
    start_offset: float,
    end_offset: float
) -> float:
    edge_length = edge.length

    return edge_length - start_offset - end_offset

def calculate_gap(
        available_length: float,
        tab_count: int,
        tab_width: float
) -> float | None:
    
    if tab_count <= 1:
        return 0.0

    remaining_length = available_length - tab_count * tab_width

    if remaining_length < 0:
        return None

    return remaining_length / (tab_count - 1)

def calculate_tab_width(
        available_length: float,
        tab_count: int,
        gap: float
) -> float | None:

    remaining_length = available_length - (tab_count - 1) * gap

    if remaining_length <= 0:
        return None

    return remaining_length / tab_count

def calculate_end_offset(
    edge_length: float,
    start_offset: float,
    tab_count: int,
    tab_width: float,
    gap: float
) -> float | None:

    occupied_length = tab_count * tab_width + (tab_count - 1) * gap

    end_offset = edge_length - start_offset - occupied_length

    if end_offset < 0:
        return None

    return end_offset