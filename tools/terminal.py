# tools/terminal.py (The Final, Unified System Interaction Tool)

import subprocess
import threading
import queue
import os
import platform
import time
from datetime import datetime
import pytz

# --- Core Classes for Managed, Stateful Terminals ---

class ManagedTerminal:
    """Represents a single, stateful, long-lived terminal session within a workspace."""
    def __init__(self, name: str, working_directory: str, output_callback=None):
        self.name = name
        self.cwd = working_directory
        self.output_callback = output_callback
        self.process = None
        self.is_running = True
        self.output_queue = queue.Queue()
        self._start_process()
        threading.Thread(target=self._read_output, args=(self.process.stdout,), daemon=True).start()
        threading.Thread(target=self._read_output, args=(self.process.stderr,), daemon=True).start()

    def _start_process(self):
        shell = 'cmd.exe' if platform.system() == "Windows" else 'bash'
        self.process = subprocess.Popen(
            [shell],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, cwd=self.cwd, bufsize=1, universal_newlines=True,
            encoding='utf-8', errors='replace'
        )
        self.log(f"Terminal '{self.name}' started with PID {self.process.pid} in '{self.cwd}'")

    def _read_output(self, pipe):
        while self.is_running and pipe.readable():
            try:
                line = pipe.readline()
                if line: self.log(line.strip())
                else: break
            except Exception: break

    def log(self, message: str):
        self.output_queue.put(message)
        if self.output_callback: self.output_callback(f"[{self.name}] {message}")

    def run_command(self, command: str) -> str:
        if not self.is_running or self.process.poll() is not None: return f"ERROR: Terminal '{self.name}' is not running."
        while not self.output_queue.empty(): self.output_queue.get()
        self.log(f"> {command}")
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()
        output_lines, last_output_time = [], time.time()
        while True:
            try:
                line = self.output_queue.get(timeout=1.0)
                output_lines.append(line)
                last_output_time = time.time()
            except queue.Empty:
                if time.time() - last_output_time > 2.0:
                    self.log("[SYSTEM] Command finished after 2.0s of inactivity.")
                    break
        return "\n".join(output_lines)

    def start_background_process(self, command: str) -> str:
        if not self.is_running or self.process.poll() is not None: return f"ERROR: Terminal '{self.name}' is not running."
        self.log(f"> {command}")
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()
        time.sleep(3)
        return f"Background command '{command}' has been sent to terminal '{self.name}'."

    def close(self):
        if self.is_running:
            self.is_running = False
            try:
                if platform.system() == "Windows": subprocess.run(f"taskkill /F /PID {self.process.pid} /T", check=True, capture_output=True, text=True)
                else: self.process.terminate()
                self.process.wait(timeout=5)
            except Exception as e: print(f"Warning: Could not cleanly terminate terminal '{self.name}': {e}")
            self.log("Terminal closed.")

class Workspace:
    def __init__(self, base_directory: str, output_callback=None):
        self.base_directory = base_directory
        os.makedirs(self.base_directory, exist_ok=True)
        self.output_callback = output_callback
        self.terminals = {}
        self.create_terminal(name="default")

    def create_terminal(self, name: str) -> str:
        if name in self.terminals: return f"Error: A terminal with the name '{name}' already exists."
        self.terminals[name] = ManagedTerminal(name, self.base_directory, self.output_callback)
        return f"Terminal '{name}' created successfully."

    def run_in_terminal(self, command: str, name: str = "default") -> str:
        if name not in self.terminals: return f"Error: No terminal with the name '{name}' found."
        return self.terminals[name].run_command(command)
        
    def start_process_in_terminal(self, command: str, name: str) -> str:
        if name not in self.terminals: return f"Error: No terminal with the name '{name}' found."
        return self.terminals[name].start_background_process(command)

    def close_all(self, exclude: list = None):
        if exclude is None: exclude = []
        for name, terminal in list(self.terminals.items()):
            if name in exclude:
                print(f"INFO: Keeping terminal '{name}' alive as requested.")
                continue
            print(f"Closing terminal '{name}'...")
            terminal.close()
            del self.terminals[name]
        print("Workspace cleanup complete.")

_WORKSPACE_INSTANCE = None
def initialize_workspace(base_directory: str, output_callback=None):
    global _WORKSPACE_INSTANCE
    if _WORKSPACE_INSTANCE is not None:
        close_workspace()
    _WORKSPACE_INSTANCE = Workspace(base_directory, output_callback)
    return _WORKSPACE_INSTANCE

def get_workspace():
    if _WORKSPACE_INSTANCE is None: return initialize_workspace(os.getcwd())
    return _WORKSPACE_INSTANCE

def close_workspace(exclude: list = None):
    global _WORKSPACE_INSTANCE
    if _WORKSPACE_INSTANCE:
        _WORKSPACE_INSTANCE.close_all(exclude=exclude)
        if not _WORKSPACE_INSTANCE.terminals: _WORKSPACE_INSTANCE = None

# --- High-Level Tool Functions for the Agent ---

def launch_application(command: str) -> str:
    """Launches a GUI application or opens a file, making it visible to the user."""
    print(f"INFO: Launching visible application with command: {command}")
    workspace = get_workspace()
    try:
        if platform.system() == "Windows":
            subprocess.Popen(f"start \"\" {command}", shell=True, cwd=workspace.base_directory)
        else:
            subprocess.Popen(f"{command} &", shell=True, cwd=workspace.base_directory)
        return f"Application/command '{command}' has been launched."
    except Exception as e:
        return f"ERROR: Failed to launch application with command '{command}'. Reason: {e}"

def create_headless_terminal(name: str) -> str:
    """Creates a new, invisible (headless) terminal session for background server processes."""
    return get_workspace().create_terminal(name)

def run_command_in_terminal(command: str, terminal_name: str = "default") -> str:
    """Runs a shell command in an existing headless terminal and waits for it to finish."""
    return get_workspace().run_in_terminal(command, terminal_name)
    
def start_server_in_terminal(command: str, terminal_name: str) -> str:
    """Starts a long-running server process in a named headless terminal."""
    return get_workspace().start_process_in_terminal(command, terminal_name)

# --- Unrelated Utility Tools ---
def get_current_datetime(timezone: str = None) -> str:
    try:
        tz = pytz.timezone(timezone) if timezone else None
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z%z")
    except Exception as e: return f"Error getting datetime: {e}"

def get_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")