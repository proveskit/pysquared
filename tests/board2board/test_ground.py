from board_connection import FCBoard
import pytest
import time
import threading
import serial
# import serial.tools.list_ports
import os


@pytest.fixture
def GRstation():
    ground_path = "Volumes/CIRCUITPY/"
    ground_port = "/dev/cu.usbmodem14201" #should probably not be hardcoded    
    #serial connect
    ground = FCBoard(ground_path, ground_port)

    # ground.send_control_c()

    t = threading.Thread(target=telemetry_logger, args=(ground, "ground_telemetry.log"), daemon=True)           
    t.start()

    yield ground
    #runs after the test is done
    ground.stop_reader_thread()
    ground.ser.close()
    t.join(timeout=2)

#currently logs to a file, but should be able to log to Github through Actions later.
def telemetry_logger(fc, file:str="fc_telemetry.log"):
    with open(file, "a") as f:
        while fc.reader_running:
                msg = fc.get_message(block=True, timeout=1)
                if msg:
                    f.write(msg + "\n")
                    f.flush()
@pytest.fixture       
def FC_Board():
    board_path = "Volumes/PYSQUARED/" 
    board_port = "/dev/cu.usbmodem14101" #should not be hardcoded
    board = FCBoard(board_path, board_port)
    print("FC board initialized")
    board.soft_reset() #should do control C, wait and control D
    print("FC board reset")
    #start the telemetry logger thread.
    t = threading.Thread(target=telemetry_logger, args=(board, "fc_telemetry.log"), daemon=True)           
    t.start()
    yield board
    board.stop_reader_thread()
    board.ser.close()
    t.join(timeout=2)

@pytest.fixture
def logger():
    print("Initializing logger")
    error_count: Counter = Counter(index=Register.error_count)
    logger: Logger = Logger(
        error_counter=error_count,
        colorized=False,
    )
    print("Logger initialized")
    return logger
    
@pytest.fixture
def uhf_packet_manager():
    packet_manager = PacketManager(
        logger,
        uhf_radio,
        config.radio.license,
        0.2,
    )
    return packet_manager


# def wait_for_new_lines(logfile, lines_before, timeout=5):
#     start = time.time()
#     while time.time() - start < timeout:
#         with open(logfile, "r") as f:
#             all_lines = f.readlines()
#         new_lines = all_lines[lines_before:]
#         if new_lines:
#             return new_lines
#         time.sleep(0.1)  # Wait a bit before checking again
#     return []

# def test_connect_to_ground_station(GRstation):
#     GRstation.get_into_repl()
#     time.sleep(1)
#     with open("ground_telemetry.log", "r") as f:
#         lines_before = len(f.readlines())
#     print("Lines before:", lines_before)
#     GRstation.send_command_to_board("print('Hello, World!')\n")

#     new_lines = wait_for_new_lines("ground_telemetry.log", lines_before, timeout=5)
#     print("New lines:", new_lines)
#     assert "Hello, World!\n" in new_lines

# # #the FC board should be reading, not executing. so we just want to make sure we are connected to it.
# def test_connect_to_fc_board(FC_Board):
#     print("Checking if FC board is connected")
#     with open("fc_telemetry.log", "r") as f:
#         assert f.read() is not None
#     print("FC board connected")


def test_beacon_format(FC_Board, GRstation):
    # Sateliete sends a beacon
    #get into the REPL to send commands
    print("Getting into the REPL")
    FC_Board.get_into_repl()

    #imports needed 
    print("Importing needed libraries")
    FC_Board.send_command_to_board("from lib.proveskit_rp2350_v5b.register import Register")
    FC_Board.send_command_to_board("from lib.pysquared.beacon import Beacon")
    FC_Board.send_command_to_board("from lib.pysquared.logger import Logger")
    FC_Board.send_command_to_board("from lib.pysquared.nvm.counter import Counter")
    FC_Board.send_command_to_board("from lib.pysquared.config.config import Config")

    #Send the beacon from the FC board
    print("Sending beacon")
    FC_Board.send_command_to_board("try: config = Config('config.json')\nexcept Exception as e: print(e)")
    FC_Board.send_command_to_board("config = Config('config.json')")
    FC_Board.send_command_to_board("boot_time = time.time()")
    FC_Board.send_command_to_board("uhf_radio = RFM9xManager(logger, config.radio, spi0, initialize_pin(logger, board.SPI0_CS0, digitalio.Direction.OUTPUT, True), initialize_pin(logger, board.RF1_RST, digitalio.Direction.OUTPUT, True))")
    FC_Board.send_command_to_board("uhf_packet_manager = PacketManager(logger, uhf_radio, config.radio.license, 0.2)")
    FC_Board.send_command_to_board("uhf_packet_manager.send(config.radio.license.encode('utf-8'))")
    FC_Board.send_command_to_board("beacon = Beacon(logger, 'cubesat_test', uhf_packet_manager, boot_time)")
    
    # listen for commands
    FC_Board.send_command_to_board("beacon.send()")
    FC_Board.send_command_to_board("cdh.listen_for_commands(10)")
    FC_Board.send_command_to_board("sleep_helper.safe_sleep(config.sleep_duration)")


    
    #ground station imports
    print("Checking if ground board is connected")
    with open("ground_telemetry.log", "r") as f:
        assert f.read() is not None

    # GRstation.enter_ground_station()

    # print("entered ground station")

    # GRstation.send_command_to_board("y")

    GRstation.send_command_to_board('1')

    print("commands sent")
#     print("FC board connected")
    # GRstation.send_command_to_board("from lib.proveskit_ground_station.proveskit_ground_station import GroundStation")
    # GRstation.send_command_to_board("from lib.pysquared.beacon import Beacon")
    # GRstation.send_command_to_board("from lib.pysquared.logger import Logger")
    # GRstation.send_command_to_board("from lib.pysquared.nvm.counter import Counter")
    # GRstation.send_command_to_board("from lib.pysquared.config.config import Config")
    # GRstation.send_command_to_board("from pysquared.cdh import CommandDataHandler")

    # #Ground station listens for the beacon
    # GRstation.send_command_to_board("try: config = Config('config.json')\nexcept Exception as e: print(e)")
    # GRstation.send_command_to_board("\n")

    # GRstation.send_command_to_board("config = Config('config.json')")
    # GRstation.send_command_to_board("from lib.proveskit_ground_station.proveskit_ground_station import GroundStation")
    # GRstation.send_command_to_board("uhf_radio = RFM9xManager(logger, config.radio, spi0, initialize_pin(logger, board.SPI0_CS0, digitalio.Direction.OUTPUT, True), initialize_pin(logger, board.RF1_RST, digitalio.Direction.OUTPUT, True))")
    # GRstation.send_command_to_board("uhf_packet_manager = PacketManager(logger, uhf_radio, config.radio.license, 0.2)")
    # GRstation.send_command_to_board("cdh = CommandDataHandler(logger, config, uhf_packet_manager)")

    # GRstation.send_command_to_board("ground_station = GroundStation(logger, config, uhf_packet_manager, cdh)")
    # GRstation.send_command_to_board("ground_station.listen()")

    time.sleep(10)

    GRstation.send_control_c()
    #assert that recieve is what you expect!
    #TODO: add assert that the beacon is received

    # make the flight controller board back to listening mode
    FC_Board.soft_reset()
    pass

def test_command_reset_send_joke():
    # Ground station sends a command to send a joke

    # FC Board receives the command

    #assert that the joke is sent
    pass

def test_command_reset_board():
    # Ground station sends a command to reset the board

    # FC Board receives the command

    #assert that the board is reset
    pass

def test_command_change_radio_modulation():
    # Ground station sends a command to change the radio modulation

    # FC Board receives the command

    #assert that the radio modulation is changed
    pass

    
