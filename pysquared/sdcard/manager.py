import os
import traceback

import sdcardio
import storage

from pysquared.logger import Logger

# type hinting only
try:
    from typing import Union

    from busio import SPI
    from microcontroller import Pin
except ImportError:
    pass

# Helpful resource: https://docs.circuitpython.org/en/latest/shared-bindings/storage/

# boot.py:
# import storage
# import json
# with open("parameters.json", "r") as f:
#    json_data = f.read()
# parameters = json.loads(json_data)
# if parameters["read_state"]:
#    storage.enable_usb_drive()
# else:
#    storage.disable_usb_drive()

# Next step: Variable needed in config file to determine USB on or off state
# (call storage.enable_usb_drive() in boot.py based on config value)


def log_to_sd(json_output: str):
    if "/logs" not in os.listdir("/sd"):
        os.chdir("/sd")
        os.mkdir("logs")
        os.chdir("/")

    session = len(os.listdir("/sd/logs"))

    # print("cuurent session number is: ", session, "continue this session or start session ", session + 1)

    print("starting new session at /sd/logs/session", session + 1)

    full_path = "/sd/logs/session" + str(session + 1)

    with open(full_path, "a") as f:
        f.write(json_output + "\n")

    print(f"Log saved to {full_path}")


class SDCardManager:
    """Class providing various functionalities related to USB and SD card operations."""

    """Initializing class, remounting storage, and initializing SD card"""

    def __init__(
        self,
        logger: Logger,
        spi_bus: SPI,
        chip_select: Pin,
        baudrate: int = 4000000,
        mount_path: str = "/sd",
        mounted: bool = False,
    ) -> None:
        # TODO: Check if directory exists before mounting, if not create it

        logger.debug("Initializing sd card")

        self.mounted = mounted

        sd = sdcardio.SDCard(spi_bus, chip_select, baudrate)
        vfs = storage.VfsFat(sd)
        storage.mount(vfs, mount_path)
        self.mounted = True

        # sys.path.append(mount_path) # Only needed if we plan to load code from the SD card without using direct imports

    # Maybe need something new like file management class to handle file operations
    # Something that might be helpful would be log rotation (rename file and create new one)
    # also log deletion
    # Due to constrained memory and radio capacity, also might be helpful to have "paginated" file reading
    # (read a certain number of lines at a time)
    def create_file(self, filename: str) -> None:
        """Creates a new file with the specified filename.

        Args:
            filename (str): The name of the file to create.
        """
        with open(filename, "w") as f:
            f.write("")

    def create_directory(self, path: str) -> None:
        """Creates a new directory at the specified path.

        Args:
            path (str): The path of the directory to create.
        """
        try:
            os.mkdir(path)
        except OSError:
            print("Directory already exists")

    def insert_data(self, filename: str, line: int, data: str) -> None:
        """Inserts data into a specific line of a file.

        Args:
            filename (str): The name of the file.
            line (int): The line number to insert data.
            data (str): The data to insert.
        """
        with open(filename, "r") as f:  # Opens file in read mode
            lines = f.readlines()  # Read all lines from file

        lines[line - 1] = data  # Replaces specified line with new data

        with open(filename, "w") as f:  # Opens file in write mode
            f.write("".join(map(str, lines)))  # Writes modified lines back to the file

    def set_sd_file_system(self) -> None:
        """Creates a file on the SD card."""
        self.make_file("/data/temperature.txt")

    def make_file(self, file_name: str, binary: bool = False) -> Union[str, None]:
        """Creates a new file in the specified directory.

        Args:
            file_name (str): The name of the file to create.
            binary (bool): If True, creates the file in binary mode.

        Returns:
            str: The name of the created file.
        """
        try:
            ff = ""
            n = 0
            _folder = file_name[
                : file_name.rfind("/") + 1
            ]  # Extracts the folder from the file name
            _file = file_name[
                file_name.rfind("/") + 1 : file_name.rfind(".")
            ]  # Extracts the file prefix from the file name
            _file_type = file_name[
                file_name.rfind(".") + 1 :
            ]  # Extracts the file type from the file name
            print(
                "Creating new file in directory: /sd{} with file prefix: {}".format(
                    _folder, _file
                )
            )
            try:
                os.chdir(
                    "/sd" + _folder
                )  # Changes the current directory to the specified folder
            except OSError:
                print("Directory {} not found. Creating...".format(_folder))
                try:
                    os.mkdir("/sd" + _folder)  # Creates the folder if it doesn't exist
                except Exception as e:
                    print(
                        "Error with creating new file: "
                        + "".join(traceback.format_exception(e))
                    )
                    return None
            for i in range(
                0xFFFF
            ):  # Finding an available, unique file name by appending a unique number
                ff = "/sd{}{}{:05}.{}".format(
                    _folder, _file, (n + i) % 0xFFFF, _file_type
                )
                try:
                    if n is not None:
                        os.stat(ff)  # Checks if the file exists
                except Exception:
                    n = (n + i) % 0xFFFF
                    # print('file number is',n)
                    break
            print("creating file..." + str(ff))
            if binary:
                b = "ab"  # Sets mode to binary append
            else:
                b = "a"  # Sets mode to append
            with open(ff, b) as f:
                f.tell()  # Returns current file position
            os.chdir("/")  # Changes back to the root directory
            return ff
        except Exception as e:
            print("Error creating file: " + "".join(traceback.format_exception(e)))
            return None

    def readfile(self, path: str, type: str = "string") -> Union[str, list]:
        """Reads a file and returns its contents.

        Args:
            path (str): The path to the file.
            type (str): The type of return value, either 'string' or 'list'.

        Returns:
            str: The contents of the file as a string or list.
        """
        with open(path, "r") as f:  # Opens the file at the specified path in read mode
            lines = (
                f.readlines()
            )  # Reads all lines from the file and stores them in a list
        if type == "list":  # Checks if the return type is specified as 'list'
            return lines  # Returns the list of lines
        if type == "string":  # Checks if the return type is specified as 'string'
            return "".join(
                map(str, lines)
            )  # Joins the list of lines into a single string and returns it

    def writefile(self, path: str, contents: str) -> str:
        """Writes contents to a file and returns the updated file contents.

        Args:
            path (str): The path to the file.
            contents (str): The contents to write to the file.

        Returns:
            str: The updated file contents.
        """
        with open(path, "w") as f:  # Opens the file at the specified path in write mode
            f.write(contents)  # Writes the provided contents to the file
        return self.readfile(path)  # Reads and returns the updated file contents

    def appendfile(self, path: str, contents: str) -> str:
        """Appends contents to a file and returns the updated file contents.

        Args:
            path (str): The path to the file.
            contents (str): The contents to append to the file.

        Returns:
            str: The updated file contents.
        """
        with open(
            path, "a+"
        ) as f:  # Opens the file at the specified path in append mode
            f.write(contents)  # Appends the provided contents to the file
        return self.readfile(path)  # Reads and returns the updated file contents

    def replace_line_in_file(self, path: str, line: int, contents: str) -> str:
        """Replaces a specific line in a file and returns the updated file contents.

        Args:
            path (str): The path to the file.
            line (int): The line number to replace.
            contents (str): The new contents for the line.

        Returns:
            str: The updated file contents.
        """
        lines = self.readfile(path, "list")  # Reads the file as a list of lines
        if not isinstance(lines, list):  # Type check to make sure lines is a list
            raise TypeError(
                "Expected lines to be a list, but got {}".format(type(lines))
            )

        if line < 1 or line > len(
            lines
        ):  # Checks if line number is in range within the file
            raise IndexError("Line number {} is out of range".format(line))

        lines[line - 1] = contents  # Replaces the specified line with the new contents
        _stringify = "".join(
            map(str, lines)
        )  # Joins the list of lines into a single string

        return self.writefile(
            path, _stringify
        )  # Writes the updated contents to the file and returns the updated file contents

    def insert_line_in_file(self, path: str, line: int, contents: str) -> str:
        """Inserts a line at a specific position in a file and returns the updated file contents.

        Args:
            path (str): The path to the file.
            line (int): The line number to insert at.
            contents (str): The contents to insert.

        Returns:
            str: The updated file contents.
        """
        lines = self.readfile(path, type="list")  # Reads the file as a list of lines
        if not isinstance(lines, list):  # Type check to make sure lines is a list
            raise TypeError(
                "Expected lines to be a list, but got {}".format(type(lines))
            )

        _intermediate = lines[
            line - 1 :
        ]  # Stores the lines from the specified position onward
        lines[line:] = _intermediate  # Shifts the lines to make space for the new line
        lines[line - 1] = contents  # Inserts the new line
        _stringify = "".join(
            map(str, lines)
        )  # Joins the list of lines into a single string

        return self.writefile(
            path, _stringify
        )  # Writes the updated contents to the file and returns the updated file contents

    def copyfile(self, to_path: str, from_path: str) -> str:
        """Copies contents from one file to another.

        Args:
            to_path (str): The destination file path.
            from_path (str): The source file path.

        Returns:
            str: The updated contents of the destination file.
        """
        # TODO: Make file if not exist. look into why from_path file get rewritten. bug?
        contents = self.readfile(from_path)  # Reads the contents of the source file
        return self.writefile(
            to_path, contents
        )  # Writes the contents to the destination file and returns the updated contents

    def print_directory(self, path: str, tabs: int = 0) -> None:
        """Prints the contents of a directory recursively.

        Args:
            path (str): The path to the directory.
            tabs (int): The number of tabs for indentation.
        """
        for file in os.listdir(path):  # Lists all files in the directory
            if file == "?":  # Skips files named "?"
                continue  # Issue noted in Learn
            stats = os.stat(path + "/" + file)  # Gets the file statistics
            filesize = stats[6]  # Gets the file size
            isdir = stats[0] & 0x4000  # Checks if the file is a directory

            if filesize < 1000:
                sizestr = str(filesize) + " by"  # Formats the file size in bytes
            elif filesize < 1000000:
                sizestr = "%0.1f KB" % (
                    filesize / 1000
                )  # Formats the file size in kilobytes
            else:
                sizestr = "%0.1f MB" % (
                    filesize / 1000000
                )  # Formats the file size in megabytes

            prettyprintname = ""
            for _ in range(tabs):
                prettyprintname += "   "  # Adds indentation based on the number of tabs
            prettyprintname += file
            if isdir:
                prettyprintname += "/"  # Adds a slash to indicate a directory
            print("{0:<40} Size: {1:>10}".format(prettyprintname, sizestr))

            # Recursively print directory contents
            if isdir:
                self.print_directory(path + "/" + file, tabs + 1)

    def delete_file(self, path: str) -> None:
        """Deletes a specified file.

        Args:
            path (str): The path to the file.
        """
        os.remove(path)  # Removes the file at the specified path

    def delete_directory(self, path: str, recursive: bool = False) -> None:
        """Deletes a specified directory.

        Args:
            path (str): The path to the directory.
            recursive (bool): If True, deletes the directory recursively.
        """
        # TODO: add recursive functionality to remove files
        # Logic to check if directory is not empty. If it is delete regardless of recursion, if it is not check for if recursion is enabled
        if path == "/sd":
            print("you really shouldnt try to delete your root directory")
        else:
            os.chdir("/sd")  # Changes the current directory to /sd
            os.rmdir(path)  # Removes the directory at the specified path
