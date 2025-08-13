# tools/workspace.py (The new core execution engine)

import subprocess
import threading
import queue
import os
import platform
import time
import re

class ManagedTerminal:
    """Represents a single, stateful, long-lived terminal session."""
    def __init__(self, name: str, working_directory: str, output_callback=None):
        self.name = name
        self.cwd = working_directory
        self.output_callback = output_callback
        self.process = None
        self.is_running = True
        self.last_prompt = ""
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
        self.log(f"Headless terminal '{self.name}' started with PID {self.process.pid}")

    def _read_output(self, pipe):
        """The ONLY function that reads from the process and logs to the UI."""
        while self.is_running:
            try:
                line = pipe.readline()
                if line:
                    stripped_line = line.strip()
                    # Check if this line is a new prompt
                    if re.match(r"^[A-Z]:\\.*>", stripped_line):
                        self.last_prompt = stripped_line
                    self.log(stripped_line)
                else:
                    break
            except:
                break

    def log(self, message: str):
        """Sends output to both the internal queue and the UI callback."""
        self.output_queue.put(message)
        if self.output_callback:
            # Prefix the message with the terminal name for the UI
            self.output_callback(f"[{self.name}] {message}")

    def log(self, message: str):
        """A simple pass-through to the UI callback."""
        if self.output_callback:
            self.output_callback(f"[{self.name}] {message}")

    def run_command(self, command: str, timeout: int = 300) -> str: # Longer base timeout
        """Sends a command and waits for it to complete by detecting idle output."""
        if not self.is_running or self.process.poll() is not None:
            return "ERROR: Terminal process is not running."

        while not self.output_queue.empty(): self.output_queue.get()
        
        self.log(f"> {command}")
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()
        
        output_lines = []
        last_output_time = time.time()
        
        # This loop will run as long as new output is being produced
        while True:
            try:
                line = self.output_queue.get(timeout=1) # Wait 1s for a line
                output_lines.append(line)
                self.log(line)
                last_output_time = time.time() # Reset idle timer on new output
            except queue.Empty:
                # If 30 seconds have passed with no new output, assume it's done.
                if time.time() - last_output_time > 30.0:
                    self.log("[SYSTEM] Command finished due to inactivity.")
                    break
        
        return "\n".join(output_lines)

    def start_server_command(self, command: str) -> str:
        """Sends a command to start a server and does NOT wait for it to finish."""
        if not self.is_running or self.process.poll() is not None:
            return "ERROR: Terminal process is not running."
        
        self.log(f"> {command}")
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()
        
        # Give it a moment to start up and log initial messages
        time.sleep(5)
        
        return f"Server command '{command}' has been sent to the terminal to run in the background."

    def close(self):
        if self.is_running:
            self.is_running = False
            try:
                if platform.system() == "Windows":
                    subprocess.run(f"taskkill /F /PID {self.process.pid} /T", check=True, capture_output=True)
                else:
                    self.process.terminate()
                self.process.wait(timeout=2)
            except Exception as e:
                print(f"Warning: Could not cleanly terminate terminal '{self.name}': {e}")
            self.log("Terminal closed.")


class Workspace:
    """Manages a collection of named terminals for a project."""
    def __init__(self, base_directory: str, output_callback=None):
        self.base_directory = base_directory
        self.output_callback = output_callback
        self.terminals = {}
        # Always start with a default terminal
        self.create_terminal("default")

    def create_terminal(self, name: str) -> str:
        if name in self.terminals:
            return f"Error: A terminal with the name '{name}' already exists."
        
        # New terminals start in the project's base directory
        self.terminals[name] = ManagedTerminal(name, self.base_directory, self.output_callback)
        return f"Terminal '{name}' created successfully."

    def run_in_terminal(self, command: str, name: str = "default") -> str:
        if name not in self.terminals:
            return f"Error: No terminal with the name '{name}' found."
        return self.terminals[name].run_command(command)

    def close_all(self):
        for name, terminal in self.terminals.items():
            print(f"Closing terminal '{name}'...")
            terminal.close()
        self.terminals = {}
        print("All workspace terminals closed.")

# --- Global Workspace Management ---
WORKSPACE_INSTANCE = None

def initialize_workspace(base_directory: str, output_callback=None) -> Workspace:
    global WORKSPACE_INSTANCE
    if WORKSPACE_INSTANCE is None:
        print(f"Initializing new workspace in {base_directory}")
        WORKSPACE_INSTANCE = Workspace(base_directory, output_callback)
    return WORKSPACE_INSTANCE

def get_workspace() -> Workspace:
    return WORKSPACE_INSTANCE

def close_workspace():
    global WORKSPACE_INSTANCE
    if WORKSPACE_INSTANCE:
        WORKSPACE_INSTANCE.close_all()
        WORKSPACE_INSTANCE = None