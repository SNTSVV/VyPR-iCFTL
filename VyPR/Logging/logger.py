"""
Module to handle logging logic.
"""

import os
import datetime
import inspect

class Log():
    """
    Class to handle logging across the VyPR codebase.
    """

    def __init__(self, directory):
        log_filename = str(datetime.datetime.now())
        self._handle = open(os.path.join(directory, log_filename), "a")
    
    def close(self):
        self._handle.close()
    
    def get_formatted_message(self, message):
        return f"[{datetime.datetime.now()}] [{inspect.stack()[2].function}] [%s] {message}\n"
    
    def info(self, message):
        self._handle.write(self.get_formatted_message(message) % "info")
    
    def debug(self, message):
        self._handle.write(self.get_formatted_message(message) % "debug")
    
    def error(self, message):
        self._handle.write(self.get_formatted_message(message) % "error")

# set up global configuration variables
log = None

def initialise_logging(directory="logs/"):
    global log
    log = Log(directory)

def end_logging():
    global log
    log.close()