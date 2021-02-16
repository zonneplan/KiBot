# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
"""
Log module

Handles logging initialization and formating.
"""
import sys
import logging
no_colorama = False
try:
    from colorama import init as colorama_init, Fore, Back, Style
except ImportError:
    no_colorama = True
# If colorama isn't installed use an ANSI basic replacement
if no_colorama:
    from .mcpyrate.ansi import Fore, Back, Style  # noqa: F811
else:
    colorama_init()
# Default domain, base name for the tool
domain = 'kilog'
filters = None


def get_logger(name=None):
    """Get a module for a submodule or the root logger if no name is
       provided"""
    # print('get_logger '+str(name))
    if name:
        return logging.getLogger(domain+'.'+name)
    return logging.getLogger(domain)


def set_domain(name):
    """Set the base name for the tool"""
    global domain
    domain = name


def set_filters(f):
    """Set the list of warning filters"""
    global filters
    filters = f


class MyLogger(logging.Logger):
    warn_hash = {}
    warn_tcnt = warn_cnt = n_filtered = 0

    def warning(self, msg, *args, **kwargs):
        MyLogger.warn_tcnt += 1
        # Get the message applying optional C style expansions
        # No longer used:
        # if isinstance(msg, str) and len(args):
        #     buf = StringIO()
        #     buf.write(msg % args)
        #     buf = buf.getvalue()
        # else:
        buf = str(msg)
        # Avoid repeated warnings
        if buf in MyLogger.warn_hash:
            MyLogger.warn_hash[buf] += 1
            return
        # Apply the filters
        if filters and buf.startswith('(W'):
            pos_end = buf.find(')')
            if pos_end > 0:
                number = int(buf[2:pos_end])
                for f in filters:
                    if f.number == number and f.regex.search(buf):
                        MyLogger.n_filtered += 1
                        return
        MyLogger.warn_cnt += 1
        MyLogger.warn_hash[buf] = 1
        if sys.version_info.major > 3 or (sys.version_info.major == 3 and sys.version_info.minor >= 8):
            super().warning(buf, stacklevel=2, **kwargs)  # pragma: no cover (Py38)
        else:
            super().warning(buf, **kwargs)

    def log_totals(self):
        if MyLogger.warn_cnt:
            filt_msg = ''
            if MyLogger.n_filtered:
                filt_msg = ', {} filtered'.format(MyLogger.n_filtered)
            self.info('Found {} unique warning/s ({} total{})'.format(MyLogger.warn_cnt, MyLogger.warn_tcnt, filt_msg))


def set_verbosity(logger, verbose, quiet):
    # Choose the log level
    log_level = logging.INFO
    if verbose:
        log_level = logging.DEBUG
    if quiet:
        log_level = logging.WARNING
    logger.setLevel(log_level)


class FilterOnlyInfo(object):
    def filter(self, record):
        return record.levelno == logging.INFO


class FilterNoInfo(object):
    def filter(self, record):
        return record.levelno != logging.INFO


def init():
    """Initialize the logging feature using a custom format"""
    # Use a class to count and filter warnings
    logging.setLoggerClass(MyLogger)
    logger = get_logger()
    # Handler for all but info.
    # Outputs to stderr
    ch = logging.StreamHandler()
    ch.addFilter(FilterNoInfo())
    ch.setFormatter(CustomFormatter(sys.stderr))
    logger.addHandler(ch)
    # Handler for t info.
    # Outputs to stdout
    ch = logging.StreamHandler(sys.stdout)
    ch.addFilter(FilterOnlyInfo())
    ch.setFormatter(CustomFormatter(sys.stdout))
    logger.addHandler(ch)
    return logger


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors"""

    def __init__(self, stream):
        super().__init__()
        if stream.isatty():
            white = Fore.WHITE
            yellow = Fore.YELLOW + Style.BRIGHT
            red = Fore.RED + Style.BRIGHT
            red_alarm = Fore.RED + Back.WHITE + Style.BRIGHT
            cyan = Fore.CYAN + Style.BRIGHT
            reset = Style.RESET_ALL
        else:
            white = ""
            yellow = ""
            red = ""
            red_alarm = ""
            cyan = ""
            reset = ""
        # format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s "
        #          "(%(filename)s:%(lineno)d)"
        format = "%(levelname)s:%(message)s (%(name)s - %(filename)s:%(lineno)d)"
        format_simple = "%(message)s"

        self.FORMATS = {
            logging.DEBUG: cyan + format + reset,
            logging.INFO: white + format_simple + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: red_alarm + format + reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
