# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Note: the algorithm used to detect the PCB outline is adapted from KiKit project.
from itertools import chain
import os
from tempfile import TemporaryDirectory
from .registrable import RegVariant
from .optionable import Optionable, PanelOptions
from .fil_base import apply_exclude_filter, apply_fitted_filter, apply_fixed_filter, apply_pre_transform
from .error import KiPlotConfigurationError
from .misc import KIKIT_UNIT_ALIASES
from .gs import GS
from .kiplot import run_command
from .macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger()


def round_point(point, precision=-4):
    return (round(point[0], precision), round(point[1], precision))


def point_str(point):
    if isinstance(point, tuple):
        return '({} mm, {} mm)'.format(GS.to_mm(point[0]), GS.to_mm(point[1]))
    return '({} mm, {} mm)'.format(GS.to_mm(point.x), GS.to_mm(point.y))


class Edge(object):
    def __init__(self, shape):
        super().__init__()
        self.start = GS.get_start_point(shape)
        self.r_start = round_point(self.start)
        self.end = GS.get_end_point(shape)
        self.r_end = round_point(self.end)
        self.shape = shape
        self.cls = shape.ShowShape()
        self.used = False

    def get_other_end(self, point):
        if self.r_start != point:
            return self.start, self.r_start
        return self.end, self.r_end

    def get_bbox(self):
        """ Get the Bounding Box for the shape, without its line width.
            KiKit uses the value in this way. """
        s = self.shape
        width = s.GetWidth()
        s.SetWidth(0)
        bbox = s.GetBoundingBox()
        s.SetWidth(width)
        return bbox

    def __str__(self):
        return '{} {}-{}'.format(self.cls, point_str(self.start), point_str(self.end))


class SubPCBOptions(PanelOptions):
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.name = ''
            """ *Name for this sub-pcb """
            self.reference = ''
            """ *Use it for the annotations method.
                This is the reference for the `kikit:Board` footprint used to identify the sub-PCB.
                Note that you can use any footprint as long as its position is inside the PCB outline.
                When empty the sub-PCB is specified using a rectangle """
            self.ref = None
            """ {reference} """
            self.tlx = 0
            """ [number|string] The X position of the top left corner for the rectangle that contains the sub-PCB """
            self.top_left_x = None
            """ {tlx} """
            self.tly = 0
            """ [number|string] The Y position of the top left corner for the rectangle that contains the sub-PCB """
            self.top_left_y = None
            """ {tly} """
            self.brx = 0
            """ [number|string] The X position of the bottom right corner for the rectangle that contains the sub-PCB """
            self.bottom_right_x = None
            """ {brx} """
            self.bry = 0
            """ [number|string] The Y position of the bottom right corner for the rectangle that contains the sub-PCB """
            self.bottom_right_y = None
            """ {bry} """
            self.units = 'mm'
            """ [millimeters,inches,mils,mm,cm,dm,m,mil,inch,in] Units used when omitted """
            self.file_id = ''
            """ Text to use as the replacement for %v expansion.
                When empty we use the parent `file_id` plus the `name` of the sub-PCB """
            self.tool = 'internal'
            """ [internal,kikit] Tool used to extract the sub-PCB. """

    def is_zero(self, val):
        return isinstance(val, (int, float)) and val == 0

    def config(self, parent):
        super().config(parent)
        if not self.name:
            raise KiPlotConfigurationError('Sub-PCB without a name')
        self.units = KIKIT_UNIT_ALIASES.get(self.units, self.units)
        if (not self.reference and self.is_zero(self.tlx) and self.is_zero(self.tly) and self.is_zero(self.brx) and
           self.is_zero(self.bry)):
            raise KiPlotConfigurationError('No reference or rectangle specified for {} sub-PCB'.format(self.name))
        self.add_units(('tlx', 'tly', 'brx', 'bry'), self.units, convert=True)
        self.board_rect = GS.create_eda_rect(self._tlx, self._tly, self._brx, self._bry)

    def get_separate_source(self):
        if self.reference:
            return "annotation; ref: {}".format(self.reference)
        return "rectangle; tlx: {}; tly: {}; brx: {}; bry: {}".format(self.tlx, self.tly, self.brx, self.bry)

    def separate_board(self, comps_hash):
        """ Apply the sub-PCB using an external tool and load it into memory """
        # Make sure kikit is available
        command = GS.ensure_tool('global', 'KiKit')
        with TemporaryDirectory(prefix='kibot-separate') as d:
            dest = os.path.join(d, os.path.basename(GS.pcb_file))
            if comps_hash:
                # Memorize the used modules
                old_modules = {m.GetReference() for m in GS.get_modules()}
            # Now do the separation
            cmd = [command, 'separate', '-s', self.get_separate_source(), GS.pcb_file, dest]
            # Execute the separate
            run_command(cmd)
            # Load this board
            GS.load_board(dest, forced=True)
            # Now reflect the changes in the list of components
            if comps_hash:
                logger.debug('Removing components outside the sub-PCB')
                # Memorize the used modules
                new_modules = {m.GetReference() for m in GS.get_modules()}
                # Compute the modules we removed
                diff = old_modules - new_modules
                logger.debugl(3, diff)
                # Exclude them from _comps
                for c in diff:
                    cmp = comps_hash[c]
                    if cmp.included:
                        cmp.included = False
                        self._excl_by_sub_pcb.add(c)
                        logger.debugl(2, '- Removing '+c)

    def _remove_items(self, iter):
        """ Remove items outside the rectangle.
            If the item has width (shapes and tracks) we discard it.
            This produces something closer to KiKit. """
        for m in iter:
            with_width = hasattr(m, 'GetWidth')
            if with_width:
                width = m.GetWidth()
                m.SetWidth(0)
            if not self.board_rect.Contains(m.GetBoundingBox()):
                GS.board.Remove(m)
                self._removed.append(m)
            if with_width:
                m.SetWidth(width)

    def _remove_modules(self, iter, comps_hash):
        """ Remove modules outside the rectangle.
            Footprints are added to the list of references to exclude.
            We also check their position, not their BBox. """
        for m in iter:
            if not self.board_rect.Contains(m.GetPosition()):
                GS.board.Remove(m)
                self._removed.append(m)
                if comps_hash:
                    self._excl_by_sub_pcb.add(m.GetReference())

    def remove_outside(self, comps_hash):
        self._removed = []
        self._remove_modules(GS.get_modules(), comps_hash)
        self._remove_items(GS.board.GetDrawings())
        self._remove_items(GS.board.GetTracks())
        self._remove_items(list(GS.board.Zones()))

    def get_pcb_edges(self):
        edges = []
        layer_cuts = GS.board.GetLayerID('Edge.Cuts')
        for edge in chain(GS.board.GetDrawings(), *[m.GraphicalItems() for m in GS.get_modules()]):
            if edge.GetLayer() != layer_cuts or edge.GetClass().startswith('PCB_DIM_') or not GS.is_valid_pcb_shape(edge):
                continue
            edges.append(Edge(edge))
        return edges

    def inform_unconnected(self, edge, point):
        raise KiPlotConfigurationError('Discontinuous PCB outline: {} not connected at {}'.format(edge, point_str(point)))

    def inform_multiple_connect(self, edges, point):
        raise KiPlotConfigurationError('PCB outline error: {}, {} and {} are connected at {}'.
                                       format(edges[0], edges[1], edges[2], point_str(point)))

    def find_contour(self, initial_edge, edges):
        # Classify the points according to its rounded coordinates
        points = {}
        for e in edges:
            points.setdefault(e.r_start, []).append(e)
            points.setdefault(e.r_end, []).append(e)
        # Look for a closed loop that contains initial_edge
        r_start = initial_edge.r_start
        start = initial_edge.start
        r_end = initial_edge.r_end
        contour = [initial_edge]
        cur_edge = initial_edge
        cur_edge.used = True
        bbox = cur_edge.get_bbox()
        while r_start != r_end:
            e = points.get(r_start, None)
            # We should get 2 points, the one we are using and its connected point
            if e is None or len(e) == 1:
                self.inform_unconnected(cur_edge, start)
            if len(e) > 2:
                self.inform_multiple_connect(e, start)
            cur_edge = e[0] if e[0] != cur_edge else e[1]
            # Sanity check
            assert not cur_edge.used
            # Change to the new segment
            contour.append(cur_edge)
            start, r_start = cur_edge.get_other_end(r_start)
            cur_edge.used = True
            bbox.Merge(cur_edge.get_bbox())
        return contour, bbox

    def search_reference_rect(self, ref):
        logger.debug('Looking for the rectangle pointed by `{}`'.format(ref))
        extra_debug = GS.debug_level > 2
        # Find the annotation component
        r = next(filter(lambda x: x.GetReference() == ref, GS.get_modules()), None)
        if r is None:
            raise KiPlotConfigurationError('Missing `{}` component in PCB, used for sub-PCB `{}`'.format(ref, self.name))
        # Find the point it indicates
        point = r.GetPosition()
        if extra_debug:
            logger.debug('- Points to '+point_str(point))
        # Look for the PCB edges
        edges = self.get_pcb_edges()
        # Detect which edge is selected
        sel_edge = next(filter(lambda x: x.shape.HitTest(point), edges), None)
        if sel_edge is None:
            raise KiPlotConfigurationError("The `{}` component doesn't select an object in the PCB edge".format(ref))
        if extra_debug:
            logger.debug('- Segment '+str(sel_edge))
        # Detect a contour containing this edge
        contour, bbox = self.find_contour(sel_edge, edges)
        if extra_debug:
            logger.debug('- BBox '+point_str(bbox.GetPosition())+'-'+point_str(bbox.GetEnd()))
            logger.debug('- Elements:')
            for e in contour:
                logger.debug(' - '+str(e))
        return bbox

    def apply(self, comps_hash):
        self._excl_by_sub_pcb = set()
        if self.tool == 'internal':
            if self.reference:
                # Get the rectangle containing the board edge pointed by the reference
                self.board_rect = self.search_reference_rect(self.reference)
            # Using a rectangle
            self.remove_outside(comps_hash)
        else:
            # Using KiKit:
            self.separate_board(comps_hash)

    def unload_board(self, comps_hash):
        # Undo the sub-PCB: just reload the PCB
        GS.load_board(forced=True)

    def restore_removed(self):
        """ Restore the stuff we removed from the board """
        for o in self._removed:
            GS.board.Add(o)

    def revert(self, comps_hash):
        if self.tool == 'internal':
            self.restore_removed()
        else:
            # Using KiKit:
            self.unload_board(comps_hash)
        # Restore excluded components
        logger.debug('Restoring components outside the sub-PCB')
        for c in self._excl_by_sub_pcb:
            comps_hash[c].included = True


class BaseVariant(RegVariant):
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.name = ''
            """ Used to identify this particular variant definition """
            self.type = ''
            """ Type of variant """
            self.comment = ''
            """ A comment for documentation purposes """
            self.file_id = ''
            """ Text to use as the replacement for %v expansion """
            # * Filters
            self.pre_transform = Optionable
            """ [string|list(string)=''] Name of the filter to transform fields before applying other filters.
                Use '_var_rename' to transform VARIANT:FIELD fields.
                Use '_var_rename_kicost' to transform kicost.VARIANT:FIELD fields.
                Use '_kicost_rename' to apply KiCost field rename rules """
            self.exclude_filter = Optionable
            """ [string|list(string)=''] Name of the filter to exclude components from BoM processing.
                Use '_mechanical' for the default KiBoM behavior """
            self.dnf_filter = Optionable
            """ [string|list(string)=''] Name of the filter to mark components as 'Do Not Fit'.
                Use '_kibom_dnf' for the default KiBoM behavior.
                Use '_kicost_dnp'' for the default KiCost behavior """
            self.dnc_filter = Optionable
            """ [string|list(string)=''] Name of the filter to mark components as 'Do Not Change'.
                Use '_kibom_dnc' for the default KiBoM behavior """
            self.sub_pcbs = SubPCBOptions
            """ [list(dict)] Used for multi-board workflows as defined by KiKit.
                I don't recommend using it, for detail read
                [this](https://github.com/INTI-CMNB/KiBot/tree/master/docs/1_SCH_2_part_PCBs).
                But if you really need it you can define the sub-PCBs here.
                Then you just use *VARIANT[SUB_PCB_NAME]* instead of just *VARIANT* """
        self._sub_pcb = None

    def config(self, parent):
        super().config(parent)
        if isinstance(self.sub_pcbs, type):
            self.sub_pcbs = []

    def get_variant_field(self):
        """ Returns the name of the field used to determine if the component belongs to the variant """
        return None

    def matches_variant(self, text):
        """ This is a generic match mechanism used by variants that doesn't really have a matching mechanism """
        return self.name.lower() == text.lower()

    def filter(self, comps):
        # Apply all the filters
        comps = apply_pre_transform(comps, self.pre_transform)
        apply_exclude_filter(comps, self.exclude_filter)
        apply_fitted_filter(comps, self.dnf_filter)
        apply_fixed_filter(comps, self.dnc_filter)
        return comps
