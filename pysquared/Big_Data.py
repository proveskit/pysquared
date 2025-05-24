import gc
import lib.adafruit_tca9548a as adafruit_tca9548a  # I2C Multiplexer
from .logger import Logger

try:
    from typing import Union
except Exception:
    pass

'''
Big_Data Module
===============

This module provides functionality for managing and interacting with satellite faces,
including initializing sensors and performing tests on all faces.
'''

class Face:
    '''
    Represents a single satellite face with associated sensors.

    Attributes:
        tca (adafruit_tca9548a.TCA9548A): The I2C multiplexer instance.
        address (int): The I2C address of the face.
        position (str): The position of the face (e.g., "x+", "y-", etc.).
        logger (Logger): Logger instance for logging errors and events.
        senlist (tuple): A tuple of sensor types available on the face.
        sensors (dict): A dictionary tracking the initialization state of sensors.
        mcp (adafruit_mcp9808.MCP9808): Temperature sensor instance (if available).
        veml (adafruit_veml7700.VEML7700): Light sensor instance (if available).
        drv (adafruit_drv2605.DRV2605): Motor driver instance (if available).
    '''
    def __init__(
        self, add: int, pos: str, tca: adafruit_tca9548a.TCA9548A, logger: Logger
    ) -> None:
        '''
        Initializes a Face instance.

        Args:
            add (int): The I2C address of the face.
            pos (str): The position of the face (e.g., "x+", "y-", etc.).
            tca (adafruit_tca9548a.TCA9548A): The I2C multiplexer instance.
            logger (Logger): Logger instance for logging errors and events.
        '''
        self.tca: adafruit_tca9548a.TCA9548A = tca
        self.address: int = add
        self.position: str = pos
        self.logger: Logger = logger

        # Use tuple instead of list for immutable data
        self.senlist: tuple = ()
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

        # Initialize sensor objects as None
        self.mcp = None
        self.veml = None
        self.drv = None

    def sensor_init(self, senlist, address) -> None:
        '''
        Initializes the sensors for the face.

        Args:
            senlist (tuple): A tuple of sensor types to initialize.
            address (int): The I2C address of the face.
        '''
        gc.collect()  # Force garbage collection before initializing sensors

        if "MCP" in senlist:
            try:
                import lib.adafruit_mcp9808 as adafruit_mcp9808

                self.mcp: adafruit_mcp9808.MCP9808 = adafruit_mcp9808.MCP9808(
                    self.tca[address], address=27
                )
                self.sensors["MCP"] = True
            except Exception as e:
                self.logger.error("Error Initializing Temperature Sensor", e)

        if "VEML" in senlist:
            try:
                import lib.adafruit_veml7700 as adafruit_veml7700

                self.veml: adafruit_veml7700.VEML7700 = adafruit_veml7700.VEML7700(
                    self.tca[address]
                )
                self.sensors["VEML"] = True
            except Exception as e:
                self.logger.error("Error Initializing Light Sensor", e)

        if "DRV" in senlist:
            try:
                import lib.adafruit_drv2605 as adafruit_drv2605

                self.drv: adafruit_drv2605.DRV2605 = adafruit_drv2605.DRV2605(
                    self.tca[address]
                )
                self.sensors["DRV"] = True
            except Exception as e:
                self.logger.error("Error Initializing Motor Driver", e)

        gc.collect()  # Clean up after initialization


class AllFaces:
    '''
    Represents all satellite faces and provides functionality to test them.

    Attributes:
        tca (adafruit_tca9548a.TCA9548A): The I2C multiplexer instance.
        faces (list[Face]): A list of Face instances.
        logger (Logger): Logger instance for logging errors and events.
    '''
    def __init__(self, tca: adafruit_tca9548a.TCA9548A, logger: Logger) -> None:
        '''
        Initializes an AllFaces instance.

        Args:
            tca (adafruit_tca9548a.TCA9548A): The I2C multiplexer instance.
            logger (Logger): Logger instance for logging errors and events.
        '''
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

    def face_test_all(self) -> list[list[float]]:
        '''
        Tests all faces and retrieves sensor data.

        Returns:
            list[list[float]]: A list of results for each face, where each result
            contains temperature and light data (or None if unavailable).
        '''
        results: list[list[float]] = []
        for face in self.faces:
            if face:
                try:
                    temp: Union[float, None] = (
                        face.mcp.temperature if face.sensors.get("MCP") else None
                    )
                    light: Union[float, None] = (
                        face.veml.lux if face.sensors.get("VEML") else None
                    )
                    results.append([temp, light])
                except Exception:
                    results.append([None, None])
        return results
