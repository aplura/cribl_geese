import os
import logging as logger
from logging import handlers
from geese.constants.configs import global_log_folder


class KennyLoggins:
    """ Base Class for Logging """

    def __init__(self, **kwargs):
        """Construct an instance of the Logging Object"""

    @staticmethod
    def get_logger(file_name, root_folder=os.getcwd(), log_level=logger.INFO):
        log_location = os.path.join(root_folder, global_log_folder)
        _log = logger.getLogger("{}".format(file_name))
        if not os.path.exists(log_location):
            os.makedirs(log_location)
        output_file_name = os.path.join(log_location, "{}.log".format(file_name))
        _log.propagate = False
        _log.setLevel(log_level)
        f_handle = handlers.RotatingFileHandler(output_file_name, maxBytes=25000000, backupCount=5)
        formatter = logger.Formatter(
            '%(asctime)s log_level=%(levelname)s pid=%(process)d tid=%(threadName)s file="%(filename)s" function="%(funcName)s" line_number="%(lineno)d" %(message)s')
        f_handle.setFormatter(formatter)
        if not len(_log.handlers):
            _log.addHandler(f_handle)
        return _log
