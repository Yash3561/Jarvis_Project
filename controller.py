# controller.py (Version 4 - Final, Unified Planner)

import threading
import traceback
import asyncio
import re
from PyQt6.QtCore import QObject, pyqtSignal
from components import speaker

class AriesController(QObject):
    # --- THESE ARE THE ONLY SIGNALS NEEDED ---
    add_message_signal = pyqtSignal(str, str, str) # role, content, raw_text
    add_terminal_output_signal = pyqtSignal(str)
    speak_signal = pyqtSignal(str)
    # The update_status_signal is no longer needed as the UI can infer status
    # from the "system" messages.

    def __init__(self, agent_instance):
        super().__init__()
        self.agent = agent_instance
        self.is_thinking = False

    def set_ui(self, ui_window):
        self.ui = ui_window
        print("INFO: Controller is now linked to the UI.")

    def update_terminal_display(self, text: str):
        self.add_terminal_output_signal.emit(text)

    def _speak(self, text: str):
        summary_match = re.search(r"<SPOKEN_SUMMARY>(.*?)</SPOKEN_SUMMARY>", text, re.DOTALL)
        if summary_match:
            spoken_summary = summary_match.group(1).strip()
            if spoken_summary:
                self.speak_signal.emit(spoken_summary)

    def process_user_query(self, query: str):
        """
        The single entry point for all user queries.
        It starts the unified agent task runner in a new thread.
        """
        if self.is_thinking:
            return
        
        self.add_message_signal.emit('user', query, query)
        # All queries now go through the single, unified agent task runner.
        threading.Thread(target=self._run_agent_task, args=(query,), daemon=True).start()

    def _run_agent_task(self, query: str):
        self.is_thinking = True
        self.add_message_signal.emit('system', 'Jarvis is thinking...', '')
        
        try:
            print("[CONTROLLER] STEP 1: Calling agent.ask()...")
            full_xml_response = asyncio.run(self.agent.ask(query))
            print("[CONTROLLER] STEP 2: Got response from agent. Removing 'thinking' message...")
            
            self.ui.run_js("document.getElementById('system-status-message')?.remove();")
            print("[CONTROLLER] STEP 3: Calling speaker...")

            self._speak(full_xml_response)
            print("[CONTROLLER] STEP 4: Speaker finished. Parsing response...")
            
            full_match = re.search(r"<FULL_RESPONSE>(.*?)</FULL_RESPONSE>", full_xml_response, re.DOTALL)
            display_content = full_match.group(1).strip() if full_match else full_xml_response
            
            print("[CONTROLLER] STEP 5: Emitting final message to UI...")
            self.add_message_signal.emit('assistant', display_content, display_content)
            print("[CONTROLLER] STEP 6: Task finished successfully.")

        except Exception:
            # If anything goes wrong, still remove the "thinking" message
            self.ui.run_js("document.getElementById('system-status-message')?.remove();")
            error_message = f"**Agent failed with a critical error:**\n\n```\n{traceback.format_exc()}\n```"
            self.add_message_signal.emit('assistant', error_message, error_message)
        finally:
            # Ensure the thinking state is always reset
            self.is_thinking = False