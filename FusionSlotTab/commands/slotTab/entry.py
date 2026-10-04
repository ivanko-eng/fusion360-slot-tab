import adsk.core
import adsk.fusion
import os

from ...lib import fusionAddInUtils as futil
from ... import config
from . import selection

app = adsk.core.Application.get()
ui = app.userInterface

# Specify the command identity information.
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_slotTab'
CMD_NAME = 'Slot and Tab'
CMD_Description = 'Create parametric slots and tabs between selected bodies.'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
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

    futil.add_handler(args.command.preSelect, selection.tab_edge_pre_select, local_handlers=local_handlers)

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

# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    # Do something interesting
    #text = text_box.text
    #expression = value_input.expression
    #msg = f'Your value: {expression}'
    #ui.messageBox(msg)

# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    #futil.log(f'{CMD_NAME} Command Preview Event')
    pass

# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    pass

# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    #futil.log(f'{CMD_NAME} Validate Input Event')
    pass
        
# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):

    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []