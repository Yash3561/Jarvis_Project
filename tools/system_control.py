# tools/system_control.py
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# --- ADD ALL OF THIS NEW CODE ---
def _get_volume_interface():
    """Helper function to get the system's master volume control."""
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))

def set_volume(level: int) -> str:
    """
    Sets the system's master volume to a specified level.
    Args:
        level (int): The desired volume level, from 0 to 100.
    """
    if not 0 <= level <= 100:
        return "ERROR: Volume level must be between 0 and 100."
    try:
        volume = _get_volume_interface()
        # The range for the library is a float from 0.0 to 1.0
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"System volume set to {level}%."
    except Exception as e:
        return f"ERROR: Could not set system volume. Details: {e}"

def get_volume() -> str:
    """Gets the current system master volume level."""
    try:
        volume = _get_volume_interface()
        level_scalar = volume.GetMasterVolumeLevelScalar()
        level_percent = int(level_scalar * 100)
        return f"Current system volume is {level_percent}%."
    except Exception as e:
        return f"ERROR: Could not get system volume. Details: {e}"

def set_screen_brightness(level: int) -> str:
    """
    Sets the primary screen brightness to a specified level.
    Args:
        level (int): The desired brightness level, from 0 to 100.
    """
    if not 0 <= level <= 100:
        return "ERROR: Brightness level must be between 0 and 100."
    try:
        sbc.set_brightness(level)
        return f"Screen brightness set to {level}%."
    except Exception as e:
        return f"ERROR: Could not set screen brightness. It may not be supported on this system. Details: {e}"

def get_screen_brightness() -> str:
    """Gets the current primary screen brightness level."""
    try:
        current_brightness = sbc.get_brightness()
        return f"Current screen brightness is {current_brightness}%."
    except Exception as e:
        return f"ERROR: Could not get screen brightness. Details: {e}"