import os
from typing import cast

import adsk.core
import adsk.fusion

from ... import config
from ...lib import fusionAddInUtils as futil

from . import (
    tab_edge_selection,
    tab_face_definition,
    tab_parameters,
    tab_preview
)

app = adsk.core.Application.get()
ui = app.userInterface

# Specify the command identity information.
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_slotTab'
CMD_NAME = 'Slot and Tab'
CMD_DESCRIPTION = 'Create parametric slots and tabs between selected bodies.'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# Specify the prompted command UI location
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons.
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

edge_labels_group = None
tab_markers_group = None

# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_DESCRIPTION, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    design, design_intent = get_design_context()

    if not design:
        return

    workflow_mode = get_workflow_mode(design_intent)
    futil.log(f'Workflow Mode: {workflow_mode}')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    inputs.addBoolValueInput('advancedEdgeFilter', 'Advanced Edge Filter', True, '', True)

    tab_edge = inputs.addSelectionInput('tabEdge', 'Tab Edge', 'Select the edge where tabs should be created.')
    
    tab_edge.addSelectionFilter('Edges')
    tab_edge.setSelectionLimits(1, 1)

    inputs.addBoolValueInput('reverseDirection', 'Reverse Direction', True, '', False)

    default_length_units = app.activeProduct.unitsManager.defaultLengthUnits
    default_value = adsk.core.ValueInput.createByString('0')

    inputs.addIntegerSpinnerCommandInput('tabCount', 'Number of Tabs', 1, 10000, 1, 1)

    distribution_mode = inputs.addDropDownCommandInput(
        'distributionMode',
        'Distribution',
        cast(adsk.core.DropDownStyles, adsk.core.DropDownStyles.TextListDropDownStyle)
    )

    distribution_mode.listItems.add('Tab Width', True)
    distribution_mode.listItems.add('Gap', False)
    distribution_mode.listItems.add('Tab Width & Gap', False)

    inputs.addValueInput('startOffsetValue', 'Start Offset', default_length_units, default_value)

    end_offset_input = inputs.addValueInput('endOffsetValue', 'End Offset', default_length_units, default_value)

    tab_width_input = inputs.addValueInput('tabWidth', 'Tab Width', default_length_units, default_value)

    tab_gap_input = inputs.addValueInput('tabGap', 'Gap', default_length_units, default_value)

    end_offset_input.isEnabled = True
    tab_width_input.isEnabled = True
    tab_gap_input.isEnabled = False

    futil.add_handler(args.command.preSelect, tab_edge_selection.tab_edge_pre_select, local_handlers=local_handlers)

    futil.add_handler(args.command.select, command_select, local_handlers=local_handlers)

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

def get_design_context():
    # Get the active design.
    design = adsk.fusion.Design.cast(app.activeProduct)

    if not design:
        ui.messageBox('No active Fusion design', 'Error')
        return None, None

    design_intent = design.designIntent
    
    futil.log(f'Design Intent: {design_intent}')

    return design, design_intent

def get_workflow_mode(design_intent):
    intent = adsk.fusion.DesignIntentTypes

    if design_intent == intent.PartDesignIntentType:
        return 'Tabs only'
    
    elif design_intent in (
        intent.AssemblyDesignIntentType,
        intent.HybridDesignIntentType
    ):
        return 'Tabs and Slots'

    return 'Unknown'

def command_select(args: adsk.core.SelectionEventArgs):
    active_input = args.activeInput

    if not active_input:
        return

    if active_input.id == 'tabEdge':
        edge = adsk.fusion.BRepEdge.cast(args.selection.entity)
        thickness_face, thickness_edges = tab_face_definition.get_adjacent_thickness_face(edge)
        futil.log(f'  Area: {adsk.fusion.BRepFace.cast(thickness_face).area}')

def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    # futil.log(f'{CMD_NAME} Command Execute Event')
    # Do something interesting
    #text = text_box.text
    #expression = value_input.expression
    #msg = f'Your value: {expression}'
    #ui.messageBox(msg)
    pass

def command_preview(args: adsk.core.CommandEventArgs):

    global edge_labels_group, tab_markers_group

    clear_preview()

    inputs = args.command.commandInputs

    edge_input = adsk.core.SelectionCommandInput.cast(
        inputs.itemById('tabEdge')
    )

    if edge_input.selectionCount == 0:
        return

    edge = adsk.fusion.BRepEdge.cast(
        edge_input.selection(0).entity
    )

    reverse_input = adsk.core.BoolValueCommandInput.cast(
        inputs.itemById('reverseDirection')
    )

    reverse = reverse_input.value

    design = adsk.fusion.Design.cast(app.activeProduct)

    try:
        # Calculate edge endpoints, respecting reverse direction
        edge_start = tab_parameters.get_point_at_distance(
            edge, 0.0, reverse
        )

        edge_end = tab_parameters.get_point_at_distance(
            edge, edge.length, reverse
        )

        # Always display edge direction labels
        edge_labels_group = tab_preview.display_edge_labels(
            design,
            edge_start,
            edge_end
        )

        positions = tab_parameters.calculate_tab_positions(
            edge,
            inputs.itemById('startOffsetValue').value,
            inputs.itemById('tabCount').value,
            inputs.itemById('tabWidth').value,
            inputs.itemById('tabGap').value,
            reverse
        )

        if positions:
            tab_markers_group = tab_preview.display_tab_points(
            design,
            positions
            )

    except (RuntimeError, ValueError) as error:
        futil.log(f'Preview error: {error}') 

def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    end_offset_input = adsk.core.ValueCommandInput.cast(inputs.itemById('endOffsetValue'))

    tab_width_input = adsk.core.ValueCommandInput.cast(inputs.itemById('tabWidth'))

    tab_gap_input = adsk.core.ValueCommandInput.cast(inputs.itemById('tabGap'))

    mode_input = adsk.core.DropDownCommandInput.cast(inputs.itemById('distributionMode'))
    selected_mode = mode_input.selectedItem.name

    if changed_input.id == 'distributionMode':
        tab_width_input.isEnabled = selected_mode in ('Tab Width', 'Tab Width & Gap')
        tab_gap_input.isEnabled = selected_mode in ('Gap', 'Tab Width & Gap')
        end_offset_input.isEnabled = selected_mode != 'Tab Width & Gap'

    should_update = (
        changed_input.id in (
            'tabEdge',
            'reverseDirection',
            'tabCount',
            'startOffsetValue',
            'distributionMode'
        )
        or (
            changed_input.id == 'tabWidth'
            and selected_mode == 'Tab Width'
        )
        or (
            changed_input.id == 'tabGap'
            and selected_mode == 'Gap'
        )
        or (
            changed_input.id in ('tabWidth', 'tabGap')
            and selected_mode == 'Tab Width & Gap'
        )
        or (
            changed_input.id == 'endOffsetValue'
            and selected_mode != 'Tab Width & Gap'
        )
    )

    if should_update:
        tab_parameters.update_tab_parameters(inputs)

def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    inputs = args.inputs

    tab_edge_input = adsk.core.SelectionCommandInput.cast(
        inputs.itemById('tabEdge')
    )

    start_offset = adsk.core.ValueCommandInput.cast(
        inputs.itemById('startOffsetValue')
    )

    end_offset = adsk.core.ValueCommandInput.cast(
        inputs.itemById('endOffsetValue')
    )

    if tab_edge_input.selectionCount == 0:
        args.areInputsValid = False
        return

    edge = adsk.fusion.BRepEdge.cast(
        tab_edge_input.selection(0).entity
    )

    if start_offset.value < 0 or end_offset.value < 0:
        args.areInputsValid = False
        return

    if start_offset.value + end_offset.value >= edge.length:
        args.areInputsValid = False
        return

    args.areInputsValid = True

def command_destroy(args: adsk.core.CommandEventArgs):

    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    global edge_labels_group, tab_markers_group

    clear_preview()
    
    local_handlers = []

def clear_preview():
    global edge_labels_group, tab_markers_group

    for group in (edge_labels_group, tab_markers_group):
        if group and group.isValid:
            group.deleteMe()

    edge_labels_group = None
    tab_markers_group = None