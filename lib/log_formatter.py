from colorama import Fore
import functools
import logging

class LogFormatter(logging.Formatter):
    LEVELS = {
        logging.CRITICAL: ("critical", Fore.LIGHTRED_EX),
        logging.ERROR: ("error", Fore.LIGHTRED_EX),
        logging.WARNING: ("warning", Fore.LIGHTYELLOW_EX),
        logging.INFO: ("info", Fore.LIGHTBLUE_EX),
        logging.DEBUG: ("debug", Fore.RESET),
    }

    @functools.cache
    def _formatter(self, module_name, level_name, level_color):
        return logging.Formatter(
            f"{level_color}{level_name}: [{module_name}] %(message)s{Fore.RESET}")

    def format(self, record):
        module_name = record.name.split(".")[-1]
        level_name, level_color = self.LEVELS.get(record.levelno)
        formatter = self._formatter(module_name, level_name, level_color)
        return formatter.format(record)
