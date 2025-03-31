# This is where the magic happens!
# This file is executed on every boot (including wake-boot from deepsleep)
# Created By: Michael Pham

"""
Built for the PySquared FC Board
Version: 2.0.0
Published: Nov 19, 2024
"""

import asyncio
import time

import digitalio
import microcontroller

try:
    from board_definitions import proveskit_rp2040_v4 as board
except ImportError:
    import board

import lib.pysquared.functions as functions
import lib.pysquared.nvm.register as register
import lib.pysquared.pysquared as pysquared
from lib.pysquared.config.config import Config
from lib.pysquared.hardware.digitalio import initialize_pin
from lib.pysquared.hardware.rfm9x.factory import RFM9xFactory
from lib.pysquared.hardware.rfm9x.manager import RFM9xManager
from lib.pysquared.logger import Logger
from lib.pysquared.nvm.counter import Counter
from lib.pysquared.nvm.flag import Flag
from lib.pysquared.rtc.rtc_common import RTC
from lib.pysquared.sleep_helper import SleepHelper
from version import __version__

RTC.init()

logger: Logger = Logger(
    error_counter=Counter(index=register.ERRORCNT, datastore=microcontroller.nvm),
    colorized=False,
)

logger.info("Booting", software_version=__version__, published_date="November 19, 2024")

loiter_time: int = 5

try:
    for i in range(loiter_time):
        logger.info(f"Code Starting in {loiter_time-i} seconds")
        time.sleep(1)

    logger.debug("Initializing Config")
    config: Config = Config("config.json")

    c = pysquared.Satellite(config, logger, __version__)

    sleep_helper = SleepHelper(c, logger)

    radio_manager = RFM9xManager(
        logger,
        Flag(index=register.FLAG, bit_index=7, datastore=microcontroller.nvm),
        RFM9xFactory(
            c.spi0,
            initialize_pin(logger, board.SPI0_CS0, digitalio.Direction.OUTPUT, True),
            initialize_pin(logger, board.RF1_RST, digitalio.Direction.OUTPUT, True),
            config.radio,
        ),
    )

    f = functions.functions(c, logger, config, sleep_helper, radio_manager)

    async def initial_boot():
        await f.beacon()
        await f.listen()

    async def critical_power_operations():
        await initial_boot()
        # Convert blocking operation to a non-blocking one using run_in_executor
        # Since this is a blocking function that will likely put the device to sleep,
        # we accept that this will block the event loop as intended
        logger.info("Entering long hibernation (this will block the event loop)")
        sleep_helper.long_hibernate()
        logger.info("Woke from long hibernation")

    async def minimum_power_operations():
        await initial_boot()
        # Same as above - this is a blocking operation by design
        logger.info("Entering short hibernation (this will block the event loop)")
        sleep_helper.short_hibernate()
        logger.info("Woke from short hibernation")

    async def send_imu_data():
        logger.info("Looking to get imu data...")
        IMUData = []
        IMUData = f.get_imu_data()
        await f.send(IMUData)

    async def main():
        await f.beacon()
        await f.listen_loiter()
        await f.state_of_health()
        await f.listen_loiter()
        f.all_face_data()
        await f.send_face()
        await f.listen_loiter()
        await send_imu_data()
        await f.listen_loiter()
        await f.joke()
        await f.listen_loiter()

    ######################### MAIN LOOP ##############################
    async def main_loop():
        """Async main loop that runs alongside the watchdog task"""
        try:
            while True:
                # L0 automatic tasks no matter the battery level
                c.check_reboot()  # Now this only checks for reboot conditions

                if c.power_mode == "critical":
                    c.rgb = (0, 0, 0)
                    await critical_power_operations()

                elif c.power_mode == "minimum":
                    c.rgb = (255, 0, 0)
                    await minimum_power_operations()

                elif c.power_mode == "normal":
                    c.rgb = (255, 255, 0)
                    await main()

                elif c.power_mode == "maximum":
                    c.rgb = (0, 255, 0)
                    await main()

                else:
                    await f.listen()

                # Small yield to allow other tasks to run
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.critical("Critical in Main Loop", e)
            time.sleep(10)
            microcontroller.on_next_reset(microcontroller.RunMode.NORMAL)
            microcontroller.reset()
        finally:
            logger.info("Going Neutral!")
            c.rgb = (0, 0, 0)
            c.hardware["WDT"] = False

    # Set up the asyncio event loop
    async def run_tasks():
        # Initialize watchdog petting task
        c.hardware["WDT"] = True
        watchdog_pet_task = asyncio.create_task(c.watchdog_pet_task())
        logger.info("Watchdog petting task created.")

        # Initialize main task
        main_task = asyncio.create_task(main_loop())

        try:
            # Wait for tasks to complete (should run forever)
            await asyncio.gather(watchdog_pet_task, main_task)
        except asyncio.CancelledError:
            logger.info("Main task was cancelled")
        except Exception as e:
            logger.critical("Error in run_tasks", e)
            raise

    # Run the asyncio event loop
    try:
        asyncio.run(run_tasks())
    except Exception as e:
        logger.critical("Error in asyncio.run", e)
        microcontroller.on_next_reset(microcontroller.RunMode.NORMAL)
        microcontroller.reset()

except Exception as e:
    logger.critical("An exception occured within main.py", e)
