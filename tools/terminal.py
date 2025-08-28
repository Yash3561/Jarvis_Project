# tools/terminal.py (V4 - The Definitive, Live-Streaming, Non-Blocking Terminal)

import subprocess
import threading
import queue
import os
import platform
import time
import uuid
from datetime import datetime
import pytz

class ManagedTerminal:
    def __init__(self, name: str, working_directory: str, output_callback=None):
        self.name = name
        self.cwd = working_directory
        self.output_callback = output_callback
        self.process = None
        self.is_running = True
        self.output_queue = queue.Queue()
        self._start_process()

        threading.Thread(target=self._read_output_pipe, args=(self.process.stdout,), daemon=True).start()
        threading.Thread(target=self._read_output_pipe, args=(self.process.stderr,), daemon=True).start()

    def _start_process(self):
        shell = 'cmd.exe' if platform.system() == "Windows" else 'bash'
        self.process = subprocess.Popen(
            [shell],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=self.cwd, bufsize=1, universal_newlines=True,
            encoding='utf-8', errors='replace'
        )
        self.log(f"Terminal '{self.name}' started with PID {self.process.pid} in '{self.cwd}'")

    def _read_output_pipe(self, pipe):
        while self.is_running and pipe and not pipe.closed:
            try:
                line = pipe.readline()
                if line:
                    self.output_queue.put(line.strip())
                else:
                    break
            except Exception:
                break

    def log(self, message: str):
        if self.output_callback:
            self.output_callback(f"[{self.name}] {message}")

    def run_command(self, command: str, timeout: int = 600) -> str:
        if not self.is_running or self.process.poll() is not None: return f"ERROR: Terminal '{self.name}' is not running."
        
        completion_marker = f"---JARVIS_COMMAND_COMPLETE_{uuid.uuid4()}---"
        full_command = f"{command} & echo {completion_marker}\n" if platform.system() != "Windows" else f"{command}\r\necho {completion_marker}\r\n"
        
        self.log(f"> {command}")
        self.process.stdin.write(full_command)
        self.process.stdin.flush()
        
        output_lines = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                line = self.output_queue.get(timeout=1.0)
                self.log(line)
                if completion_marker in line:
                    self.log(f"[SYSTEM] Command completed successfully.")
                    break
                if line:
                    output_lines.append(line)
            except queue.Empty:
                continue
        else:
            return "ERROR: Command timed out."

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
                if self.process:
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

    def run_in_terminal(self, command: str, name: str = "default", timeout: int = 600) -> str:
        if name not in self.terminals: return f"Error: No terminal with the name '{name}' found."
        return self.terminals[name].run_command(command, timeout=timeout)
        
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
    if _WORKSPACE_INSTANCE is not None: close_workspace()
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

def launch_application(command: str) -> str:
    print(f"INFO: Launching visible application with command: {command}")
    workspace = get_workspace()
    try:
        if platform.system() == "Windows":
            subprocess.Popen(f"start cmd /c \"{command}\"", shell=True, cwd=workspace.base_directory)
        else:
            subprocess.Popen(f"{command} &", shell=True, cwd=workspace.base_directory)
        return f"Application/command '{command}' has been launched."
    except Exception as e: return f"ERROR: Failed to launch application: {e}"

def create_headless_terminal(name: str) -> str:
    return get_workspace().create_terminal(name)
def run_command_in_terminal(command: str, terminal_name: str = "default", timeout: int = 600) -> str:
    return get_workspace().run_in_terminal(command, terminal_name, timeout)
def start_server_in_terminal(command: str, terminal_name: str) -> str:
    return get_workspace().start_process_in_terminal(command, terminal_name) # THIS WAS THE TYPO

def get_current_datetime(timezone: str = None) -> str:
    try:
        tz = pytz.timezone(timezone) if timezone else None
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z%z")
    except Exception as e: return f"Error getting datetime: {e}"
def get_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")