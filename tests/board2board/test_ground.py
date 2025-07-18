from board_connection import FCBoard
import pytest
import time
import threading


@pytest.fixture
def GRstation():
    ground_path = ""
    ground_port = "/dev/serial/" #should probably not be hardcoded    
    #serial connect
    ground = FCBoard(ground_path, ground_port)
    #get into repl (only for ground station, FC board will always be reading, not executing)
    ground.get_into_repl()

    yield ground
    #runs after the test is done
    ground.stop_reader_thread()
    ground.ser.close()

#currently logs to a file, but should be able to log to Github through Actions later.
@pytest.fixture
def telemetry_logger(fc):
    with open("fc_telemetry.log", "a") as f:
        while fc.reader_running:
                msg = fc.get_message(block=True, timeout=1)
                if msg:
                    f.write(msg + "\n")

@pytest.fixture       
def FC_Board():
    board_path = "" 
    board_port = "/dev/serial/" #should probably not be hardcoded
    board = FCBoard(board_path, board_port)

    #start the telemetry logger thread.
    t = threading.Thread(target=telemetry_logger, args=(board,), daemon=True)           
    t.start()
    yield board
    board.stop_reader_thread()
    board.ser.close()
    t.join(timeout=2)



def test_beacon_format(self):
    # Ground station sends a beacon

    # FC Board receieves 

    #assert that recieve is what you expect
    pass

