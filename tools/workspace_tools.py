# In a tool file like tools/system_commands.py or a new workspace_tools.py

from .workspace import get_workspace

def create_terminal(name: str) -> str:
    """Creates a new, named terminal session. Use this to run concurrent processes like a backend and frontend server."""
    workspace = get_workspace()
    if not workspace:
        return "ERROR: Workspace not initialized."
    return workspace.create_terminal(name)

def run_command(command: str, terminal_name: str = "default") -> str:
    """Runs a shell command in a specified terminal. If no name is given, uses the 'default' terminal."""
    workspace = get_workspace()
    if not workspace:
        return "ERROR: Workspace not initialized."
    return workspace.run_in_terminal(command, terminal_name)