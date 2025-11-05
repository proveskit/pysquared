"""Demo code file for testing supervisor.set_next_code_file functionality.

This file demonstrates the set_next_code_file command by petting the watchdog
at a 1-second interval. This is a simple example to verify that the supervisor
module can successfully switch to a new code file after a reset.

To use this demo:
1. Upload this file to the satellite's filesystem (e.g., as 'watchdog_demo.py')
2. Send a command to set this as the next code file:
   {"password": "<password>", "name": "<satellite_name>", "command": "set_next_code_file", "args": ["watchdog_demo.py"]}
3. The satellite will reset and begin executing this file instead of the default code.py

Note: This is a minimal demonstration. In a real scenario, you would want to
include more robust error handling and a way to revert to the original code.
"""

import time

import microcontroller
import watchdog

# Initialize the watchdog
wdt = watchdog.WatchDogTimer(timeout=5.0)

print("Starting watchdog demo - petting watchdog every 1 second")
print(f"Watchdog timeout: {wdt.timeout} seconds")
print("Press Ctrl+C to stop (or let it timeout if you want to test watchdog reset)")

iteration = 0
try:
    while True:
        # Pet the watchdog
        wdt.feed()
        iteration += 1
        print(f"[{iteration}] Watchdog petted at {time.monotonic():.2f}s")

        # Sleep for 1 second
        time.sleep(1.0)

except KeyboardInterrupt:
    print("\nDemo stopped by user")
except Exception as e:
    print(f"Error in watchdog demo: {e}")
    # In a real scenario, you might want to reset to the original code file here
    microcontroller.reset()
