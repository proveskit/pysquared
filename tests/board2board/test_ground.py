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
    ground_port = "/dev/cu.usbmodem14101" #should probably not be hardcoded    
    #serial connect
    ground = FCBoard(ground_path, ground_port)

    ground.get_into_repl()

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

@pytest.fixture       
def FC_Board():
    board_path = "Volumes/PYSQUARED/" 
    board_port = "/dev/cu.usbmodem14201" #should not be hardcoded
    board = FCBoard(board_path, board_port)
    board.soft_reset() #should do control C, wait and control D
    #start the telemetry logger thread.
    t = threading.Thread(target=telemetry_logger, args=(board, "fc_telemetry.log"), daemon=True)           
    t.start()
    yield board
    board.stop_reader_thread()
    board.ser.close()
    t.join(timeout=2)

def test_connect_to_ground_station(GRstation):
    time.sleep(1)
    # Get current line count before sending command
    with open("ground_telemetry.log", "r") as f:
        lines_before = len(f.readlines())
        
    print("Lines before:", lines_before)
    time.sleep(1) # need to wait for command to be on board
    GRstation.send_command_to_board("print('Hello, World!')")
    time.sleep(1)
    # Read only new lines from the telemetry log file
    with open("ground_telemetry.log", "r") as f:
        all_lines = f.readlines()
        new_lines = all_lines[lines_before-2:]  # -1 for the first line, -1 for the >>> 
        
    assert "Hello, World!\n" in new_lines

#the FC board should be reading, not executing. so we just want to make sure we are connected to it.
def test_connect_to_fc_board(FC_Board):
    with open("fc_telemetry.log", "r") as f:
        assert f.read() is not None


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

    
