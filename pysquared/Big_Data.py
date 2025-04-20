import gc

import adafruit_tca9548a as adafruit_tca9548a  # I2C Multiplexer
from adafruit_drv2605 import DRV2605
from adafruit_mcp9808 import MCP9808
from adafruit_veml7700 import VEML7700

from .logger import Logger


class Face:
    mcp: MCP9808
    veml: VEML7700
    drv: DRV2605

    def __init__(
        self, add: int, pos: str, tca: adafruit_tca9548a.TCA9548A, logger: Logger
    ) -> None:
        self.tca: adafruit_tca9548a.TCA9548A = tca
        self.address: int = add
        self.position: str = pos
        self.logger: Logger = logger

        # Define sensors based on position using a dictionary lookup instead of if-elif chain
        sensor_map: dict[str, tuple[str, ...]] = {
            "x+": ("MCP", "VEML", "DRV"),
            "x-": ("MCP", "VEML"),
            "y+": ("MCP", "VEML", "DRV"),
            "y-": ("MCP", "VEML"),
            "z-": ("MCP", "VEML", "DRV"),
        }
        self.senlist: tuple[str, ...] = sensor_map.get(pos, ())

        # Initialize sensor states dict only with needed sensors
        self.sensors: dict[str, bool] = {sensor: False for sensor in self.senlist}

    def sensor_init(self, senlist, address) -> None:
        gc.collect()  # Force garbage collection before initializing sensors

        if "MCP" in senlist:
            try:
                self.mcp = MCP9808(self.tca[address], address=27)
                self.sensors["MCP"] = True
            except Exception as e:
                self.logger.error("Error Initializing Temperature Sensor", e)

        if "VEML" in senlist:
            try:
                self.veml = VEML7700(self.tca[address])
                self.sensors["VEML"] = True
            except Exception as e:
                self.logger.error("Error Initializing Light Sensor", e)

        if "DRV" in senlist:
            try:
                import adafruit_drv2605 as adafruit_drv2605

                self.drv = adafruit_drv2605.DRV2605(self.tca[address])
                self.sensors["DRV"] = True
            except Exception as e:
                self.logger.error("Error Initializing Motor Driver", e)

        gc.collect()  # Clean up after initialization


class AllFaces:
    def __init__(self, tca: adafruit_tca9548a.TCA9548A, logger: Logger) -> None:
        self.tca: adafruit_tca9548a.TCA9548A = tca
        self.faces: list[Face] = []
        self.logger: Logger = logger

        # Create faces using a loop instead of individual variables
        positions: list[tuple[str, int]] = [
            ("y+", 0),
            ("y-", 1),
            ("x+", 2),
            ("x-", 3),
            ("z-", 4),
        ]
        for pos, addr in positions:
            face: Face = Face(addr, pos, tca, self.logger)
            face.sensor_init(face.senlist, face.address)
            self.faces.append(face)
            gc.collect()  # Clean up after each face initialization

    def face_test_all(self) -> list[list[float | None]]:
        results: list[list[float | None]] = []
        for face in self.faces:
            if face:
                try:
                    temp: float | None = (
                        face.mcp.temperature if face.sensors.get("MCP") else None
                    )
                    light: float | None = (
                        face.veml.lux if face.sensors.get("VEML") else None
                    )
                    results.append([temp, light])
                except Exception:
                    results.append([None, None])
        return results
