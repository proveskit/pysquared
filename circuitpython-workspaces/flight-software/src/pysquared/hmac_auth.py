"""This module provides HMAC-based authentication for command messages.

This module implements HMAC (Hash-based Message Authentication Code) for
authenticating commands sent to the satellite. It provides protection against
unauthorized commands and replay attacks through the use of a shared secret
and packet counter.

**Usage:**
```python
from pysquared.hmac_auth import HMACAuthenticator

# On the ground station
authenticator = HMACAuthenticator("shared_secret_key")
message = '{"command": "send_joke", "name": "MySat"}'
counter = 42
hmac_value = authenticator.generate_hmac(message, counter)

# On the satellite
authenticator = HMACAuthenticator("shared_secret_key")
is_valid = authenticator.verify_hmac(message, counter, hmac_value)
```
"""

import hmac

try:
    # CircuitPython uses adafruit_hashlib
    import adafruit_hashlib as hashlib
except ImportError:
    # Standard Python uses hashlib
    import hashlib


class HMACAuthenticator:
    """Provides HMAC authentication for command messages."""

    def __init__(self, secret_key: str) -> None:
        """Initializes the HMACAuthenticator.

        Args:
            secret_key: The shared secret key for HMAC generation and verification.
        """
        self._secret_key: bytes = secret_key.encode("utf-8")

    def generate_hmac(self, message: str, counter: int) -> str:
        """Generates an HMAC for a message with a counter.

        Args:
            message: The message to authenticate.
            counter: The packet counter for replay attack prevention.

        Returns:
            The HMAC as a hexadecimal string.
        """
        # Combine message and counter
        data = f"{message}|{counter}".encode("utf-8")

        # Generate HMAC using SHA-256
        # Note: In CircuitPython, this uses the circuitpython_hmac library
        # In testing/CPython, this uses the standard hmac library
        h = hmac.new(self._secret_key, data, hashlib.sha256)
        return h.hexdigest()

    def verify_hmac(self, message: str, counter: int, received_hmac: str) -> bool:
        """Verifies an HMAC for a message with a counter.

        Args:
            message: The message to verify.
            counter: The packet counter for replay attack prevention.
            received_hmac: The HMAC to verify.

        Returns:
            True if the HMAC is valid, False otherwise.
        """
        expected_hmac = self.generate_hmac(message, counter)
        return hmac.compare_digest(expected_hmac, received_hmac)
