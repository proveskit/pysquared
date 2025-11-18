# Flight Software Examples

This directory contains example code files demonstrating various PySquared features.

## watchdog_demo.py

A simple demonstration of the `set_next_code_file` command functionality. This file can be used to test the supervisor module's ability to switch execution to a different code file after a reset.

### What it does:
- Prints status messages to the console every 1 second
- Demonstrates that the new code file is running after reset
- Runs in an infinite loop (simulating continuous operation)

### How to use:
1. Upload this file to your satellite's filesystem
2. Send a `set_next_code_file` command with this file as the argument:
   ```json
   {
     "password": "your_password",
     "name": "your_satellite_name",
     "command": "set_next_code_file",
     "args": ["watchdog_demo.py"]
   }
   ```
3. The satellite will reset and begin executing this file instead of the default `code.py`
4. You should see messages like `[1] Running at 1.23s` printed every second

### Reverting back to normal operation:
To return to the default code file, you would need to:
- Either send another `set_next_code_file` command with `code.py` as the argument
- Or manually reset the satellite and ensure `code.py` is present

**Note:** This is a minimal demonstration. In production, you should include mechanisms to safely revert to the original code if the new code fails to execute properly.
