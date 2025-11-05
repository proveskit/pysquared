"""Demo code file for testing supervisor.set_next_code_file functionality.

This file demonstrates the set_next_code_file command with a simple loop that
prints messages at a 1-second interval. This is a minimal example to verify that
the supervisor module can successfully switch to a new code file after a reset.

To use this demo:
1. Upload this file to the satellite's filesystem (e.g., as 'watchdog_demo.py')
2. Send a command to set this as the next code file:
   {"password": "<password>", "name": "<satellite_name>", "command": "set_next_code_file", "args": ["watchdog_demo.py"]}
3. The satellite will reset and begin executing this file instead of the default code.py

Note: This is a minimal demonstration. In a real scenario, you would want to
include more robust error handling and a way to revert to the original code.
"""

import time

print("=== Watchdog Demo Started ===")
print("This demonstrates the set_next_code_file command functionality.")
print("Printing a message every 1 second to show the code is running.")
print("Press Ctrl+C to stop.")

iteration = 0
try:
    while True:
        iteration += 1
        current_time = time.monotonic()
        print(f"[{iteration}] Running at {current_time:.2f}s")

        # Sleep for 1 second
        time.sleep(1.0)

except KeyboardInterrupt:
    print("\n=== Demo stopped by user ===")
except Exception as e:
    print(f"Error in demo: {e}")
    import microcontroller

    microcontroller.reset()
