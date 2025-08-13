# tools/persistent_terminal.py (V4 - Truly Stateful with a Single Process)

import subprocess
import threading
import queue
import os
import platform
import sys
import time

class PersistentTerminal:
    def __init__(self, working_directory=None, output_callback=None): # Add callback here
        self.process = None
        self.is_running = True
        self.output_queue = queue.Queue()
        self.base_directory = working_directory or os.getcwd()
        self.output_callback = output_callback # Store the callback
        self._start_process()

        self.stdout_thread = threading.Thread(target=self._read_output, args=(self.process.stdout,), daemon=True)
        self.stderr_thread = threading.Thread(target=self._read_output, args=(self.process.stderr,), daemon=True)
        self.stdout_thread.start()
        self.stderr_thread.start()

    def _start_process(self):
        """Starts ONE SINGLE, long-lived shell process."""
        shell = 'cmd.exe' if platform.system() == "Windows" else 'bash'
        self.process = subprocess.Popen(
            [shell],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.base_directory,
            bufsize=1, # Line-buffered
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )
        print(f"INFO: Stateful terminal process started with PID {self.process.pid} in {self.base_directory}")

    def _read_output(self, pipe):
        while self.is_running:
            try:
                line = pipe.readline()
                if line:
                    line_stripped = line.strip()
                    self.output_queue.put(line_stripped)
                    # --- THE NEW CONNECTION ---
                    # If we have a phone line, use it to send the output in real time
                    if self.output_callback:
                        self.output_callback(line_stripped)
                else:
                    break # Pipe closed
            except:
                break

    def run_command(self, command: str, timeout: int = 30) -> str:
        """Sends a command to the persistent shell and collects the output."""
        if not self.is_running or self.process.poll() is not None:
            return "ERROR: Terminal process is not running."

        # Clear any stale output
        while not self.output_queue.empty(): self.output_queue.get()

        # This is the core change: we just write to the stdin of our ONE process
        print(f"INFO: > Sending command to stateful terminal: {command}")
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()
        
        output_lines = []
        start_time = time.time()
        
        # Intelligent output collection loop
        while time.time() - start_time < timeout:
            try:
                line = self.output_queue.get(timeout=0.2) # Wait briefly for new lines
                output_lines.append(line)
                # Reset idle timer if we get output
                start_time = time.time()
            except queue.Empty:
                # If the queue is empty for 2 seconds, assume the command is done.
                # This is crucial for handling both quick commands and long-running servers.
                if time.time() - start_time > 2.0:
                    break
        
        return "\n".join(output_lines) if output_lines else f"Command '{command}' executed. (No output after 2s idle)"


    def close(self):
        """Shuts down the terminal process cleanly."""
        if self.is_running:
            self.is_running = False
            try:
                if platform.system() == "Windows":
                    # taskkill is more reliable for closing cmd trees on Windows
                    subprocess.run(f"taskkill /F /PID {self.process.pid} /T", check=True, capture_output=True)
                else:
                    self.process.terminate()
                self.process.wait(timeout=2)
            except Exception as e:
                print(f"Warning: Could not cleanly terminate terminal process: {e}")
            print("INFO: Stateful terminal closed.")

# --- Global Instance Management (No Changes Needed) ---
TERMINAL_INSTANCE = None
def get_terminal(working_directory: str = None, output_callback=None) -> PersistentTerminal:
    global TERMINAL_INSTANCE
    if TERMINAL_INSTANCE is None:
        # Pass the callback when creating the instance
        TERMINAL_INSTANCE = PersistentTerminal(working_directory=working_directory, output_callback=output_callback)
    return TERMINAL_INSTANCE

def run_in_terminal(command: str) -> str:
    term = get_terminal()
    return term.run_command(command)

def close_terminal() -> str:
    global TERMINAL_INSTANCE
    if TERMINAL_INSTANCE:
        TERMINAL_INSTANCE.close()
        TERMINAL_INSTANCE = None
    return "Terminal session closed."