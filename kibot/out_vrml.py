# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Salvador E. Tropea
# Copyright (c) 2022-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiAuto
    role: mandatory
    version: 2.1.0
"""
import os
from .gs import GS
from .out_base_3d import Base3DOptionsWithHL, Base3D
from .misc import FAILED_EXECUTE
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


def replace_ext(file, ext):
    file, ext = os.path.splitext(file)
    return file+'.wrl'


class VRMLOptions(Base3DOptionsWithHL):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=vrml, %x=wrl) """
            self.dir_models = 'shapes3D'
            """ Subdirectory used to store the 3D models for the components.
                If you want to create a monolithic file just use '' here.
                Note that the WRL file will contain relative paths to the models """
            self.use_pcb_center_as_ref = True
            """ The center of the PCB will be used as reference point.
                When disabled the `ref_x`, `ref_y` and `ref_units` will be used """
            self.ref_x = 0
            """ X coordinate to use as reference when `use_pcb_center_as_ref` is disabled """
            self.ref_y = 0
            """ Y coordinate to use as reference when `use_pcb_center_as_ref` is disabled """
            self.ref_units = 'millimeters'
            """ [millimeters,inches'] Units for `ref_x` and `ref_y` """
            self.model_units = 'millimeters'
            """ [millimeters,meters,deciinches,inches] Units used for the VRML (1 deciinch = 0.1 inches) """
        super().__init__()
        self._expand_id = 'vrml'
        self._expand_ext = 'wrl'

    def get_targets(self, out_dir):
        targets = [self._parent.expand_filename(out_dir, self.output)]
        if self.dir_models:
            # Missing models can be downloaded during the 3D variant filtering
            # Also renamed or disabled.
            # # We will also generate the models
            # dir = os.path.join(out_dir, self.dir_models)
            # filtered = {os.path.join(dir, os.path.basename(replace_ext(m, 'wrl')))
            #    for m in self.list_models(even_missing=True)}
            # targets.extend(list(filtered))
            # So we just add the dir
            targets.append(os.path.join(out_dir, self.dir_models))
        return targets

    def get_pcb_center(self):
        center = GS.board.ComputeBoundingBox(True).Centre()
        return self.to_mm(center.x), self.to_mm(center.y)

    def run(self, name):
        command = self.ensure_tool('KiAuto')
        super().run(name)
        self.apply_show_components()
        board_name = self.filter_components(highlight=set(self.expand_kf_components(self.highlight)), force_wrl=True)
        self.undo_show_components()
        cmd = [command, 'export_vrml', '--output_name', os.path.basename(name), '-U', self.model_units]
        if self.dir_models:
            cmd.extend(['--dir_models', self.dir_models])
        if not self.use_pcb_center_as_ref or GS.ki5:
            # KiCad 5 doesn't support using the center, we emulate it
            if self.use_pcb_center_as_ref and GS.ki5:
                x, y = self.get_pcb_center()
                units = 'millimeters'
            else:
                x = self.ref_x
                self.ref_y
                units = self.ref_units
            cmd.extend(['-x', str(x), '-y', str(x), '-u', units])
        cmd.extend([board_name, os.path.dirname(name)])
        # Execute it
        self.exec_with_retry(self.add_extra_options(cmd), FAILED_EXECUTE)


@output_class
class VRML(BaseOutput):  # noqa: F821
    """ VRML (Virtual Reality Modeling Language)
        Exports the PCB as a 3D model (WRL file).
        This is intended for rendering, unlike STEP which is intended to be
        an exact mechanic model """
    def __init__(self):
        super().__init__()
        self._category = 'PCB/3D'
        with document:
            self.options = VRMLOptions
            """ *[dict] Options for the `vrml` output """

    @staticmethod
    def get_conf_examples(name, layers, templates):
        return Base3D.simple_conf_examples(name, 'PCB in VRML format', '3D')
