from pcbnew import (GERBER_WRITER)
from .out_any_drill import (AnyDrill)
from kiplot.macros import macros, output_class  # noqa: F401


@output_class
class Gerb_Drill(AnyDrill):
    """ Gerber drill format
        This is the information for the drilling machine in gerber format.
        You can create a map file for documentation purposes.
        This output is what you get from the 'File/Fabrication output/Drill Files' menu in pcbnew. """
    def __init__(self, name, type, description):
        super(Gerb_Drill, self).__init__(name, type, description)

    def _configure_writer(self, board, offset):
        drill_writer = GERBER_WRITER(board)
        # hard coded in UI?
        drill_writer.SetFormat(5)
        drill_writer.SetOptions(offset)
        return drill_writer
