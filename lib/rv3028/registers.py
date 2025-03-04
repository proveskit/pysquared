"""
Register and flag definitions for the RV-3028-C7 RTC module.
https://www.microcrystal.com/fileadmin/Media/Products/RTC/App.Manual/RV-3028-C7_App-Manual.pdf

Author: Davit Babayan
"""


class Reg:
    SECONDS = 0x00
    MINUTES = 0x01
    HOURS = 0x02
    WEEKDAY = 0x03
    DATE = 0x04
    MONTH = 0x05
    YEAR = 0x06
    ALARM_MINUTES = 0x07
    ALARM_HOURS = 0x08
    ALARM_WEEKDAY = ALARM_DATE = 0x09  # Depends on which one is enabled
    TIMER0 = 0x0A
    TIMER1 = 0x0B
    TIMER_STATUS0 = 0x0C  # readonly
    TIMER_STATUS1 = 0x0D  # readonly
    STATUS = 0x0E
    CONTROL1 = 0x0F
    CONTROL2 = 0x10
    GP_BITS = 0x11
    CLOCK_INT_MASK = 0x12
    EVENT_CONTROL = 0x13
    TIMESTAMP_COUNT = 0x14  # readonly
    TIMESTAMP_SECONDS = 0x15  # readonly
    TIMESTAMP_MINUTES = 0x16  # readonly
    TIMESTAMP_HOURS = 0x17  # readonly
    TIMESTAMP_DATE = 0x18  # readonly
    TIMESTAMP_MONTH = 0x19  # readonly
    TIMESTAMP_YEAR = 0x1A  # readonly
    UNIX_TIME0 = 0x1B
    UNIX_TIME1 = 0x1C
    UNIX_TIME2 = 0x1D
    UNIX_TIME3 = 0x1E
    RAM1 = 0x1F
    RAM2 = 0x20
    EEDATA = 0x26
    EECMD = 0x27
    ID = 0x28  # readonly
    EEPROM_CLKOUT = 0x35
    EEPROM_OFFSET = 0x36
    EEPROM_BACKUP = 0x37


class Flag:
    SET = 1
    CLEAR = 0


class Alarm:
    """
    Contains bit masks for the alarm registers.
    The alarm registers that contain these flags are ALARM_MINUTES, ALARM_HOURS, and ALARM_DATE.
    """

    DISABLED = 0x80  # This is a flag that you should set to disable the alarm.
    VALUE = 0x7F  # Enable the alarm and store the value.
    VALUE_SIZE = 7  # Number of bits of value


class Status:
    """
    Contains bit masks for the status register. Generally, these should be READ, not written to.
    The exception is clearing the flags, since they do not clear themselves.
    """

    PORF = 0x01  # 0: No voltage drop, 1: Voltage drop (if set to 0 after POR, default is 1)
    EVENT = 0x02  # Enabled if an event is detected
    ALARM = 0x04  # Enabled if an alarm is triggered
    TIMER = 0x08  # Enabled if a periodic countdown timer event is triggered.
    UPDATE = 0x10  # Enabled if a periodic time update event is triggered.
    BACKUP_SWITCH = 0x20  # Enabled if a switch from main to backup power occurs.
    CLOCK_OUTPUT = 0x40  # Enabled if there is an interrupt on the clock output pin.
    EEBUSY = 0x80  # Enabled if the EEPROM is handling a read/write request.


class Control1:
    """
    Contains bit masks for the control1 register.
    - This register is used to specify the target for the Alarm Interrupt function and the Periodic Time Update Interrupt
    function and to select or set operations for the Periodic Countdown Timer.
    """

    FREQ_SELECT = 0x03  # 2 bit flag. Uses the FreqSelect enum for values.
    TIMER_ENABLE = 0x04  # Starts the countdown timer if 1.
    EEPROM_REFRESH_DISABLE = 0x08  # Disables the automatic EEPROM refresh if 1.
    UPDATE_INT_SELECT = 0x10  # 0: second updates (default). 1: minute updates.
    WADA = 0x20  # 0: use weekday for alarm (default). 1: use date for alarm.
    TIMER_REPEAT = 0x80  # 0: Single mode, halt countdown when it reaches 0 (default). 1: repeat timer.


class TimerFreq:
    """
    Selections for the frequency of the timer countdown clock.
    """

    SIZE = 2  # Number of bits used for the frequency selection
    FREQ_4096HZ = 0x00  # Default value
    FREQ_64HZ = 0x01
    FREQ_1HZ = 0x10
    FREQ_60S = 0x11


class Control2:
    """
    Contains bit masks for the control2 register.
    - This register is used to control the interrupt event output for the INT pin, the stop/start status of clock and calendar
    operations, the interrupt controlled clock output on CLKOUT pin, the hour mode and the time stamp enable.
    """

    RESET = (
        0x01  # 0: Normal operation. 1: software based time adjustment (see datasheet).
    )
    HOUR_MODE = 0x02  # 0: 24 hour mode (default). 1: 12 hour mode.
    EVENT_INT_ENABLE = (
        0x04  # Enables the event interrupt on the INT pin (disabled by default).
    )
    ALARM_INT_ENABLE = (
        0x08  # Enables the alarm interrupt on the INT pin (disabled by default).
    )
    TIMER_INT_ENABLE = (
        0x10  # Enables the timer interrupt on the INT pin (disabled by default).
    )
    UPDATE_INT_ENABLE = (
        0x20  # Enables the update interrupt on the INT pin (disabled by default).
    )
    CLOCK_OUTPUT_INT_ENABLE = (
        0x40  # Enables the clock output interrupt on the INT pin (disabled by default).
    )
    TIMESTAMP_ENABLE = 0x80  # Enables the timestamp function (disabled by default).


class GPBits:
    GPR_MASK = 0x7F  # General purpose bits. Can be used for any purpose.


class ClockIntOn:
    """
    Contains bit masks for the clock interrupt mask register.
    - This register is used to select a predefined interrupt for automatic clock output. Setting a bit to 1 selects the
    corresponding interrupt.

    Example Usage: `clock_int_mask = ClockIntOn.TIMER | ClockIntOn.ALARM`
    """

    SIZE = 2
    TIME_UPDATE = 0x01  # Enables the periodic time update interrupt.
    TIMER = 0x02  # Enables the countdown timer interrupt.
    ALARM = 0x04  # Enables the alarm interrupt.
    EVENT = 0x08  # Enables the event interrupt.


class EventControl:
    """
    Contains bit masks for the event control register.
    - This register controls the event detection on the EVI pin. Depending of the EHL bit, high or low level (or rising or
    falling edge) can be detected. Moreover a digital glitch filtering can be applied to the EVI signal by selecting a
    sampling period tSP in the ET field. Furthermore this register holds control functions for the Time Stamp data. And
    the switching over to VBACKUP Power state can be selected as source for an event.
    """

    TIMESTAMP_SOURCE_SELECT = 0x01  # 0: Timestamp source is external event. 1: Timestamp source is the backup switchover.
    TIMESTAMP_OVERWRITE = (
        0x02  # 0: Timestamp is not overwritten. 1: Timestamp is overwritten.
    )
    TIMESTAMP_RESET = (
        0x04  # 0: Timestamp is not reset. 1: Reset all seven TS registers.
    )
    EVENT_FILTER = 0x30  # 2 bit flag. Uses the EventFilter enum for values.
    EVENT_HIGH_LOW_SELECT = (
        0x40  # 0: Low level or falling edge. 1: High level or rising edge.
    )


class EventFilter:
    """
    Selections for the event filter.
    """

    SIZE = 2
    FILTER_OFF = 0x00  # Default value
    FILTER_256Hz = 0x01
    FILTER_64Hz = 0x02
    FILTER_8Hz = 0x03


class EEPROMClockOut:
    """
    Contains bit masks for the EEPROM clock out register.
    - A programmable square wave output is available at CLKOUT pin. Clock output can be controlled by the CLKOE bit
    (or by the CLKF flag) (see PROGRAMMABLE CLOCK OUTPUT). After a Power up and the first refreshment time
    tPREFR = ~66 ms, the EEPROM Clkout values CLKOE, CLKSY, PORIE and FD are copied from the EEPROM to the
    corresponding RAM mirror. The default values preset on delivery are: CLKOUT = enabled, synchronization enabled,
    F = 32.768 kHz.
    """

    FREQ_SELECT: 0x07  # 3 bit flag. Uses the FreqSelect enum for values.
    POR_INT_ENABLE = (
        0x08  # 0: POR interrupt disabled (default). 1: POR interrupt enabled.
    )
    CLKOUT_SYNC_ENABLE = 0x40  # 0: Synchronization disabled. 1: Synchronization enable/disable enabled (default).
    CLKOUT_ENABLE = 0x80  # 0: Clock output pin LOW. 1: Clock output on CLKOUT pin enabled (default).


class FreqSelect:
    """
    Selections for the frequency of the clock in CLKOUT.
    - 8192 Hz to 1 Hz clock pulses and the timer interrupt pulses can be affected by compensation pulses
    """

    SIZE = 3
    FREQ_32768HZ = 0x00  # Default value
    FREQ_8192HZ = 0x01
    FREQ_1024HZ = 0x02
    FREQ_64HZ = 0x03
    FREQ_32HZ = 0x04
    FREQ_1HZ = 0x05
    PREDEFINED = 0x06  #  CLKSY bit has no effect
    LOW = 0x07


class EEPROMBackup:
    """
    Contains bit masks for the EEPROM backup register.
    - This register is used to control the switchover function and the trickle charger and it holds bit 0 (LSB) of the EEOffset
    value. The preconfigured (Factory Calibrated) EEOffset value may be changed by the user.
    After a Power up and the first refreshment time tPREFR = ~66 ms, the EEPROM Backup value is copied from the
    EEPROM to the corresponding RAM mirror.
    """

    TRICKLE_CHARGE_RES = 0x03  # 2 bit flag representing trickle charge resistance. Uses the Resistance enum for values.
    BACKUP_SWITCHOVER = 0x0C  # 2 bit flag representing backup switchover mode. Uses the BSM enum for values.
    TRICKLE_CHARGE_ENABLE = (
        0x20  # 0: Trickle charger disabled (default). 1: Trickle charger enabled.
    )
    BACKUP_SWITCHOVER_INT_ENABLE = 0x40  # 0: Backup switchover interrupt disabled (default). 1: Backup switchover interrupt enabled.
    EEOFFSET_LSB = (
        0x80  # LSB of the EEOffset value (see EEPROM OFFSET REGISTER in datasheet)
    )
    FEDE = 0x10  # FOR THE LOVE OF GOD, NEVER DISABLE THIS.


class Resistance:
    """
    Selections for the resistance of the trickle charger.
    """

    SIZE = 2
    RES_3000 = 0x00  # Default value (ohms)
    RES_5000 = 0x01
    RES_9000 = 0x02
    RES_15000 = 0x03


class BSM:
    """
    Selections for the backup switchover mode.
    """

    SIZE = 2
    DISABLED_DEFAULT = 0x00  # Default value
    DIRECT = 0x01
    DISABLED = 0x02
    LEVEL = 0x03


class EECMD:
    """
    Contains commands for the EEPROM.
    - This register must be written with specific values, in order to Update or Refresh all (readable/writeable) Configuration
    EEPROM registers or to read or write from/to a single EEPROM Memory byte.
    - Before using this commands, the automatic refresh function has to be disabled (EERD = 1) and the busy status bit
    EEbusy has to indicate, that the last transfer has been finished (EEbusy = 0). Before entering the command 11h,
    12h, 21h or 22h, EECMD has to be written with RESET.
    """

    RESET = 0x00  # Reset command (must always be sent first).
    UPDATE = 0x11  # Sends data from configuration RAM to EEPROM.
    REFRESH = 0x12  # Sends data from EEPROM to configuration RAM.
    WRITE_ONE_BYTE = 0x21  # Writes one byte to the EEPROM from EEDATA.
    READ_ONE_BYTE = 0x22  # Reads one byte from the EEPROM to EEDATA.


class ID:
    """
    Contains the ID of the RTC module.
    - This register holds the 4 bit Hardware Identification number (HID) and the 4 bit Version Identification number (VID).
    """

    VID = 0x0F  # Version Identification number
    HID = 0xF0  # Hardware Identification number
