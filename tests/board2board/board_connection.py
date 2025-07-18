import serial
import time
import os
import threading
import queue

# Configure the serial connection
baud_rate = 9600  # Adjust baud rate as needed

class FCBoard:
    def __init__(self, board_file_path, board_port):
        # board_port = None
        self.message_queue = queue.Queue()
        self.reader_running = False
        self.reader_thread = None
        self.board_file_path = board_file_path
        self.board_port = board_port
        try:
            # Look through the by-id directory for the board port if it has space in it
            # by_id_dir = '/dev/serial/by-id/'
            # for device in os.listdir(by_id_dir):
            #     if 'space' in device.lower():
            #         board_port = os.path.join(by_id_dir, device)
            #         break
            # else:
            #     raise FileNotFoundError("No device with 'Space' found in /dev/serial/by-id/")
            # TODO: add a way to find the board port if it is not provided. The above code works for the raspberry pi (Linux) but when we have two boards, who knows if it would detect the right one that starts with space.

            # Open the serial connection
            ser = serial.Serial(self.board_port, baud_rate, timeout=1)
            print(f"Connected to board at {self.board_port}")
            self.ser = ser
            
            # Start the reader thread
            self.start_reader_thread()

        except KeyboardInterrupt:
            print("\nExiting...")

        except serial.SerialException as e:
            print(f"Error: {e}")


    def get_into_repl(self):
            # need to send this to start the board
            time.sleep(1)
            self.send_command_to_board('\03')
            time.sleep(1)
            self.send_command_to_board('a')

    
    def reader_worker(self):
        """Background thread that continuously reads from the serial port"""
        self.reader_running = True
        try:
            while self.reader_running:
                if self.ser and self.ser.is_open:
                    data = self.ser.readline()
                    if data:
                        message = data.decode().strip()
                        self.message_queue.put(message)
                    time.sleep(0.01)  # Small delay to prevent CPU overuse
        except Exception as e:
            print(f"Reader thread error: {e}, {self.ser}")
        finally:
            self.reader_running = False
            print("Reader thread stopped")
    
    def start_reader_thread(self):
        """Start the background serial reader thread"""
        if not self.reader_running:
            self.reader_thread = threading.Thread(
                target=self.reader_worker, 
                daemon=True
            )
            self.reader_thread.start()
            print("Message reader thread started")
    
    def stop_reader_thread(self):
        """Stop the background reader thread"""
        self.reader_running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=2.0)
            if self.reader_thread.is_alive():
                print("Warning: Reader thread did not terminate cleanly")
    
    def has_messages(self):
        """Check if there are messages in the queue"""
        return not self.message_queue.empty()
    
    def get_message(self, block=False, timeout=None):
        """
        Get a message from the queue
        
        Args:
            block (bool): Whether to block until a message is available
            timeout (float): Timeout in seconds when block=True
            
        Returns:
            str or None: Message from the board, or None if no message is available
        """
        try:
            return self.message_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
    
    def get_all_messages(self):
        """Get all available messages from the queue"""
        messages = []
        while not self.message_queue.empty():
            messages.append(self.message_queue.get())
        return messages
    
    def send_command_to_board(self, command):
        output = ""
        try:
            if command.lower() == 'exit':
                    print("Exiting...")
                    
            else:
                # Send the command to the board
                self.ser.write((command + '\r\n').encode())
                self.ser.flush()

            # Read response from the board
            
            return 1 

        except KeyboardInterrupt:
            print("\nExiting...")

        except serial.SerialException as e:
            print(f"Error: {e}")
        except Exception as e:
            self.ser.close()
            raise e



    
    def soft_reset(self):
        self.send_command_to_board('\03')
        time.sleep(1)
        self.send_command_to_board('\04')
        time.sleep(1)

                


# if __name__ == "__main__":
#     main()
