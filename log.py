import sys
import logging

from settings import LOG_LEVEL, LOG_FMT, LOG_DATEFMT, LOG_FILENAME


class Logger(object):
    def __init__(self):
        self._logger = logging.getLogger()
        self.formatter = logging.Formatter(fmt=LOG_FMT, datefmt=LOG_DATEFMT)
        self._logger.addHandler(self._get_file_handler(LOG_FILENAME))
        self._logger.addHandler(self._get_console_handler())
        self._logger.setLevel(LOG_LEVEL)

        self._suppress_debug_logging('selenium.webdriver.remote.remote_connection')
        self._suppress_debug_logging('urllib3.connectionpool')
        self._suppress_debug_logging('webdriver_manager')
        self._suppress_debug_logging('WDM') 


    def _get_file_handler(self, filename):
        '''return a file handler that writes logs to a file'''
        file_handler = logging.FileHandler(filename=filename, encoding="utf-8")
        file_handler.setFormatter(self.formatter)
        return file_handler

    def _get_console_handler(self):
        '''return a console handler that writes logs to console'''
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.formatter)
        return console_handler
    
    def _suppress_debug_logging(self, logger_name):
        '''Set specified logger to WARNING level to suppress debug and info messages'''
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    @property
    def logger(self):
        return self._logger


logger = Logger().logger

if __name__ == '__main__':
    logger.debug("Debug Message")
    logger.info("Info Message")
    logger.warning("Warning Message")
    logger.error("Error Message")
    logger.critical("Critical Message")