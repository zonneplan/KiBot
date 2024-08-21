# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnologïa Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
#
# Helper functions to catch the Python logging system and send it to a wxWidgets window

import wx
import wx.lib.newevent
import logging
from .. import log

# create event type
wxLogEvent, EVT_WX_LOG_EVENT = wx.lib.newevent.NewEvent()
log_handler = None


# https://stackoverflow.com/questions/2819791/how-can-i-redirect-the-logger-to-a-wxpython-textctrl-using-a-custom-logging-hand
class wxLogHandler(logging.Handler):
    """ A handler class which sends log strings to a wx object """
    def __init__(self, wxDest=None):
        """
        Initialize the handler
        @param wxDest: the destination object to post the event to
        @type wxDest: wx.Window
        """
        logging.Handler.__init__(self)
        self.wxDest = wxDest
        self.level = logging.DEBUG

    def flush(self):
        """ does nothing for this handler """

    def emit(self, record):
        """ Emit a record. """
        try:
            msg = self.format(record)
            evt = wxLogEvent(message=msg, levelname=record.levelname)
            wx.PostEvent(self.wxDest, evt)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


def start_gui_log(dest):
    global log_handler
    log_handler = log.set_log_handler(wxLogHandler(dest))


def stop_gui_log():
    global log_handler
    if log_handler:
        log.remove_log_handler(log_handler)
        log_handler = None
