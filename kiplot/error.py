"""
KiPlot errors
"""


class KiPlotError(Exception):
    pass


class PlotError(KiPlotError):
    pass


class KiPlotConfigurationError(KiPlotError):
    pass
