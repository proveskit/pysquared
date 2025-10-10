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

import adafruit_hashlib as hashlib  # interesting, this lib imports cpython stuff if it's available.... hmmm
from circuitpython_hmac import HMAC


class HMACAuthenticator:
    """Provides HMAC authentication for command messages."""

    def __init__(self, secret_key: str, hmac_class=HMAC) -> None:
        """Initializes the HMACAuthenticator.

        Args:
            secret_key: The shared secret key for HMAC generation and verification.
        """
        self._secret_key: bytes = secret_key.encode("utf-8")
        self._hmac_class = hmac_class

    def generate_hmac(self, message: str, counter: int) -> str:
        """Generates an HMAC for a message with a counter.

        Args:
            message: The message to authenticate.
            counter: The packet counter for replay attack prevention.

        Returns:
            The HMAC as a hexadecimal string.
        """
        # Combine message and counter
        print("generating hmac")
        print("hamc class", self._hmac_class)
        data = f"{message}|{counter}".encode("utf-8")

        # Generate HMAC using SHA-256
        # Note: In CircuitPython, this uses the circuitpython_hmac library
        # In testing/CPython, this uses the standard hmac library
        h = self._hmac_class(self._secret_key, data, hashlib.sha256)
        return h.hexdigest()

    @staticmethod
    def compare_digest(expected_hmac: str, received_hmac: str):
        """Compares two byte or str sequences in constant time.
        Returns True if expected_hmac == received_hmac, False otherwise.
        """
        print("comparing digest")

        if not isinstance(expected_hmac, (str, bytes)):
            expected_hmac = str(expected_hmac)

        if isinstance(expected_hmac, str):
            expected_hmac = expected_hmac.encode("utf-8")

        # Ensure received_hmac is bytes
        if not isinstance(received_hmac, (str, bytes)):
            received_hmac = str(received_hmac)

        if isinstance(received_hmac, str):
            received_hmac = received_hmac.encode("utf-8")

        print("expected:", expected_hmac)
        print("received:", received_hmac)

        if len(expected_hmac) != len(received_hmac):
            print("lens are da same")
            # Continue processing full length to keep timing consistent
            result = 0
            maxlen = max(len(expected_hmac), len(received_hmac))
            for i in range(maxlen):
                x = expected_hmac[i] if i < len(expected_hmac) else 0
                y = received_hmac[i] if i < len(received_hmac) else 0
                result |= x ^ y
            print("returning False")
            return False
        else:
            print("not the if")
        print("result is")
        result = 0
        for x, y in zip(expected_hmac, received_hmac):
            result |= x ^ y
        return result == 0

    def verify_hmac(self, message: str, counter: int, received_hmac: str) -> bool:
        """Verifies an HMAC for a message with a counter.

        Args:
            message: The message to verify.
            counter: The packet counter for replay attack prevention.
            received_hmac: The HMAC to verify.

        Returns:
            True if the HMAC is valid, False otherwise.
        """
        print("verifying hmac")
        expected_hmac = self.generate_hmac(message, counter)
        print("expected hmac", expected_hmac)
        print("expected hmac type", type(expected_hmac))

        return HMACAuthenticator.compare_digest(expected_hmac, received_hmac)
