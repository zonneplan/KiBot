# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
import os
from pcbnew import PLOT_FORMAT_SVG, FromMM, ToMM
from .drill_marks import DrillMarks
from .gs import GS
from .kicad.patch_svg import change_svg_viewbox
from .misc import KICAD5_SVG_SCALE
from .out_base import PcbMargin
from .out_any_layer import AnyLayer
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class SVGOptions(DrillMarks):
    def __init__(self):
        super().__init__()
        with document:
            self.line_width = 0.25
            """ [0.02,2] For objects without width [mm] (KiCad 5) """
            self.mirror_plot = False
            """ Plot mirrored """
            self.negative_plot = False
            """ Invert black and white """
            self.svg_precision = 4
            """ [0,6] Scale factor used to represent 1 mm in the SVG (KiCad 6).
                The value is how much zeros has the multiplier (1 mm = 10 power `svg_precision` units).
                Note that for an A4 paper Firefox 91 and Chrome 105 can't handle more than 5 """
            self.limit_viewbox = False
            """ When enabled the view box is limited to a selected area """
            self.size_detection = 'kicad_edge'
            """ [kicad_edge,kicad_all] Method used to detect the size of the view box.
                The `kicad_edge` method uses the size of the board as reported by KiCad,
                components that extend beyond the PCB limit will be cropped. You can manually
                adjust the margin to make them visible.
                The `kicad_all` method uses the whole size reported by KiCad. Usually includes extra space.
                See `limit_viewbox` option """
            self.margin = PcbMargin
            """ [number|dict] Margin around the view box [mm].
                Using a number the margin is the same in the four directions.
                See `limit_viewbox` option """
        self._plot_format = PLOT_FORMAT_SVG

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        po.SetMirror(self.mirror_plot)
        if GS.ki5:
            po.SetLineWidth(FromMM(self.line_width))
        po.SetNegative(self.negative_plot)
        if GS.ki6:
            po.SetSvgPrecision(self.svg_precision, False)

    def read_vals_from_po(self, po):
        super().read_vals_from_po(po)
        if GS.ki5:
            self.line_width = ToMM(po.GetLineWidth())
        self.negative_plot = po.GetNegative()
        self.mirror_plot = po.GetMirror()

    def config(self, parent):
        super().config(parent)
        # Margin
        self.margin = PcbMargin.solve(self.margin)

    def run(self, output_dir, layers):
        super().run(output_dir, layers)
        if not self.limit_viewbox:
            return
        # Limit the view box of the SVG
        bbox = GS.board.ComputeBoundingBox(self.size_detection == 'kicad_edge').getWxRect()
        # Apply the margin (left right top bottom)
        bbox = (bbox[0]-self.margin[0], bbox[1]-self.margin[2],
                bbox[2]+self.margin[0]+self.margin[1], bbox[3]+self.margin[2]+self.margin[3])
        # Width/height of the used area in cm
        width = ToMM(bbox[2])*0.1
        height = ToMM(bbox[3])*0.1
        # Scale factor to convert KiCad IU to the SVG units
        mult = KICAD5_SVG_SCALE if GS.ki5 else 10.0 ** (self.svg_precision - 6)
        # View port in SVG units
        bbox = tuple(map(lambda x: int(x*mult), bbox))
        logger.debug('Adjusting SVG viewBox to {} for width {} cm and height {} cm'.format(bbox, width, height))
        for f in self._generated_files.values():
            fname = os.path.join(output_dir, f)
            logger.debugl(2, '- '+f)
            change_svg_viewbox(fname, bbox, width, height)


@output_class
class SVG(AnyLayer):
    """ SVG (Scalable Vector Graphics)
        Exports the PCB to a format suitable for 2D graphics software.
        Unlike bitmaps SVG drawings can be scaled without losing resolution.
        This output is what you get from the File/Plot menu in pcbnew.
        The `pcb_print` is usually a better alternative. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = SVGOptions
            """ *[dict] Options for the `svg` output """
        self._category = 'PCB/docs'
