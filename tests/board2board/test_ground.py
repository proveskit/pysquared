from board_connection import FCBoard
import pytest
import time
import threading
import serial
# import serial.tools.list_ports
import os

#commening out because I am just testing the flight controller board
# @pytest.fixture
# def GRstation():
#     ground_path = "Volumes/CIRCUITPY/"
#     ground_port = "/dev/cu.usbmodem14201" #should not be hardcoded    
#     #serial connect
#     ground = FCBoard(ground_path, ground_port)

#     ground.get_into_repl()

#     t = threading.Thread(target=telemetry_logger, args=(ground), daemon=True)           
#     t.start()

#     #time.sleep(10)

#     yield ground
#     #runs after the test is done
#     ground.stop_reader_thread()
    # ground.ser.close()

#currently logs to a file, but should be able to log to Github through Actions later.
def telemetry_logger(fc, file:str="fc_telemetry.log"):
    with open(file, "a") as f:
        while fc.reader_running:
                msg = fc.get_message(block=True, timeout=1)
                if msg:
                    f.write(msg + "\n")

@pytest.fixture       
def FC_Board():
    board_path = "Volumes/PYSQUARED/" 
    board_port = "/dev/cu.usbmodem14201" #should not be hardcoded
    board = FCBoard(board_path, board_port)
    board.soft_reset() #should do control C, wait and control D
    #start the telemetry logger thread.
    t = threading.Thread(target=telemetry_logger, args=(board,), daemon=True)           
    t.start()
    yield board
    board.stop_reader_thread()
    board.ser.close()
    t.join(timeout=2)

# def test_connect_to_ground_station(GRstation):
#     time.sleep(1)
#     print(GRstation.get_all_messages()) # need to wait for past commands to be on board so we can clear them out
#     time.sleep(1) # need to wait for command to be on board
#     GRstation.get_message() # this should be print('Hello, World!') That I called above.
#     assert GRstation.get_message() == "Hello, World!"

#the FC board should be reading, not executing. so we just want to make sure we are connected to it.
def test_connect_to_fc_board(FC_Board):
    assert FC_Board.get_all_messages() is not None


def test_beacon_format():
    # Ground station sends a beacon

    # FC Board receieves 

    #turn on the radio so it recer

    #assert that recieve is what you expect
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

    
