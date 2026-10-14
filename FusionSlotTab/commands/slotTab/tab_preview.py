import adsk.core
import adsk.fusion

def display_edge_labels(
    design: adsk.fusion.Design,
    edge_start: adsk.core.Point3D,
    edge_end: adsk.core.Point3D
):
    group = design.rootComponent.customGraphicsGroups.add()
    group.name = 'Edge Direction Preview'

    add_point_label(group, edge_start, 'Start')
    add_point_label(group, edge_end, 'End')

    return group

def add_point_label(
    group: adsk.fusion.CustomGraphicsGroup,
    point: adsk.core.Point3D,
    label: str
):
    transform = adsk.core.Matrix3D.create()
    transform.translation = point.asVector()

    text = group.addText(label, 'Arial', 0.3, transform)

    billboard = adsk.fusion.CustomGraphicsBillBoard.create(point)
    
    text.billBoarding = billboard
    text.isSelectable = False

    return text

def display_tab_points(
    design: adsk.fusion.Design,
    positions: list
):
    group = design.rootComponent.customGraphicsGroups.add()
    group.name = 'Tab Position Preview'

    size = 0.1

    start_coords = []
    end_coords = []

    for start_point, end_point in positions:

        for point, coordinates in (
            (start_point, start_coords),
            (end_point, end_coords)
        ):
            x, y, z = point.x, point.y, point.z

            # X-axis
            coordinates.extend([
                x - size, y, z,
                x + size, y, z
            ])

            # Y-axis
            coordinates.extend([
                x, y - size, z,
                x, y + size, z
            ])

            # Z-axis
            coordinates.extend([
                x, y, z - size,
                x, y, z + size
            ])

    # Green start markers
    if start_coords:
        coords = adsk.fusion.CustomGraphicsCoordinates.create(start_coords)
        lines = group.addLines(coords, [], False)

        green = adsk.core.Color.create(0, 184, 92, 255)
        lines.color = adsk.fusion.CustomGraphicsSolidColorEffect.create(green)

    # Red end markers
    if end_coords:
        coords = adsk.fusion.CustomGraphicsCoordinates.create(end_coords)
        lines = group.addLines(coords, [], False)

        red = adsk.core.Color.create(255, 80, 80, 255)
        lines.color = adsk.fusion.CustomGraphicsSolidColorEffect.create(red)

    return group