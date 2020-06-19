from pcbnew import (GERBER_WRITER)
from .out_base import (BaseOutput)
from .out_any_drill import (AnyDrill)


class GerbDrill(AnyDrill):
    def __init__(self, name, type, description):
        super(GerbDrill, self).__init__(name, type, description)

    def _configure_writer(self, board, offset):
        drill_writer = GERBER_WRITER(board)
        # hard coded in UI?
        drill_writer.SetFormat(5)
        drill_writer.SetOptions(offset)
        return drill_writer


# Register it
BaseOutput.register('gerb_drill', GerbDrill)
