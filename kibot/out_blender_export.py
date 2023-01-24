# -*- coding: utf-8 -*-
# Copyright (c) 2023 Salvador E. Tropea
# Copyright (c) 2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: Blender
    role: mandatory
    version: 3.4.0
"""
from copy import copy
import json
import os
from tempfile import NamedTemporaryFile, TemporaryDirectory
from .error import KiPlotConfigurationError
from .kiplot import get_output_targets, run_output, run_command, register_xmp_import, config_output, configure_and_run
from .gs import GS
from .optionable import Optionable, BaseOptions
from .out_base_3d import Base3D, Base3DOptionsWithHL
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
bb = None


def get_board_size():
    global bb
    if bb is None:
        bb = GS.board.ComputeBoundingBox(True)
    width = GS.to_mm(bb.GetWidth())/1000.0
    height = GS.to_mm(bb.GetHeight())/1000.0
    size = max(width, height)
    return width, height, size


class PCB2BlenderOptions(Optionable):
    """ How the PCB3D is imported """
    def __init__(self, field=None):
        super().__init__()
        with document:
            self.components = True
            """ Import the components """
            self.cut_boards = True
            """ Separate the sub-PCBs in separated 3D models """
            self.texture_dpi = 1016.0
            """ [508-2032] Texture density in dots per inch """
            self.center = True
            """ Center the PCB at the coordinates origin """
            self.enhance_materials = True
            """ Create good looking materials """
            self.merge_materials = True
            """ Reuse materials """
            self.solder_joints = "SMART"
            """ [NONE,SMART,ALL] The plug-in can add nice looking solder joints.
                This option controls if we add it for none, all or only for THT/SMD pads with solder paste """
            self.stack_boards = True
            """ Move the sub-PCBs to their relative position """
        self._unkown_is_error = True


class BlenderOutputOptions(Optionable):
    """ What is generated """
    def __init__(self, field=None):
        super().__init__()
        with document:
            self.type = 'render'
            """ *[fbx,obj,x3d,gltf,stl,ply,blender,render] The format for the output.
                The `render` type will generate a PNG image of the render result.
                `fbx` is Kaydara's Filmbox, 'obj' is the Wavefront, 'x3d' is the new ISO/IEC standard
                that replaced VRML, `gltf` is the standardized GL format, `stl` is the 3D printing
                format, 'ply' is Polygon File Format (Stanford).
                Note that some formats includes the light and camera and others are just the 3D model
                (i.e. STL and PLY) """
            self.output = GS.def_global_output
            """ Name for the generated file (%i='3D_blender_$VIEW' %x=VARIABLE).
                The extension is selected from the type """
        self._unkown_is_error = True


class BlenderLightOptions(Optionable):
    """ A light in the scene. Currently also for the camera """
    def __init__(self, field=None):
        super().__init__()
        with document:
            self.name = ""
            """ Name for the light """
            self.pos_x = 0
            """ [number|string] X position [m]. You can use `width`, `height` and `size` for PCB dimensions """
            self.pos_y = 0
            """ [number|string] Y position [m]. You can use `width`, `height` and `size` for PCB dimensions """
            self.pos_z = 0
            """ [number|string] Z position [m]. You can use `width`, `height` and `size` for PCB dimensions """
        self._unkown_is_error = True

    def solve(self, member):
        val = getattr(self, member)
        if not isinstance(val, str):
            return float(val)
        try:
            res = eval(val, {}, {'width': self._width, 'height': self._width, 'size': self._size})
        except Exception as e:
            raise KiPlotConfigurationError('wrong `{}`: `{}`\nPython says: `{}`'.format(member, val, str(e)))
        return res

    def config(self, parent):
        super().config(parent)
        self._width, self._height, self._size = get_board_size()
        self.pos_x = self.solve('pos_x')
        self.pos_y = self.solve('pos_y')
        self.pos_z = self.solve('pos_z')


class BlenderRenderOptions(Optionable):
    """ Render parameters """
    def __init__(self, field=None):
        super().__init__()
        with document:
            self.samples = 10
            """ *How many samples we create. Each sample is a raytracing render.
                Use 1 for a raw preview, 10 for a draft and 100 or more for the final render """
            self.resolution_x = 1280
            """ Width of the image """
            self.resolution_y = 720
            """ Height of the image """
            self.transparent_background = False
            """ *Make the background transparent """
            self.background1 = "#66667F"
            """ First color for the background gradient """
            self.background2 = "#CCCCE5"
            """ Second color for the background gradient """
        self._unkown_is_error = True


class PCB3DExportOptions(Base3DOptionsWithHL):
    """ Options to generate the PCB3D file """
    def __init__(self, field=None):
        super().__init__()
        with document:
            self.output = GS.def_global_output
            """ Name for the generated PCB3D file (%i='blender_export' %x='pcb3d') """
            self.version = '2.1'
            """ [2.1,2.1_haschtl] Variant of the format used """
        self._expand_id = 'blender_export'
        self._expand_ext = 'pcb3d'
        self._unkown_is_error = True


class Blender_ExportOptions(BaseOptions):
    _views = {'top': 'z', 'bottom': 'Z', 'front': 'y', 'rear': 'Y', 'right': 'x', 'left': 'X'}
    _rviews = {v: k for k, v in _views.items()}

    def __init__(self):
        with document:
            self.pcb3d = PCB3DExportOptions
            """ *[string|dict] Options to export the PCB to Blender.
                You can also specify the name of the output that generates the PCB3D file.
                See the `PCB2Blender_2_1` and  `PCB2Blender_2_1_haschtl` templates """
            self.pcb_import = PCB2BlenderOptions
            """ Options to configure how Blender imports the PCB.
                The default values are good for most cases """
            self.outputs = BlenderOutputOptions
            """ [dict|list(dict)] Outputs to generate in the same run """
            self.light = BlenderLightOptions
            """ [dict|list(dict)] Options for the light/s """
            self.add_default_light = True
            """ Add a default light when none specified.
                The default light is located at (-size*3.33, size*3.33, size*5) where size is max(width, height) of the PCB """
            self.camera = BlenderLightOptions
            """ [dict] Options for the camera.
                If none specified KiBot will create a suitable camera """
            self.render_options = BlenderRenderOptions
            """ *[dict] How the render is done for the `render` output type """
            self.rotate_x = 0
            """ Angle to rotate the board in the X axis, positive is clockwise [degrees] """
            self.rotate_y = 0
            """ Angle to rotate the board in the Y axis, positive is clockwise [degrees] """
            self.rotate_z = 0
            """ Angle to rotate the board in the Z axis, positive is clockwise [degrees] """
            self.view = 'top'
            """ *[top,bottom,front,rear,right,left,z,Z,y,Y,x,X] Point of view.
                Compatible with `render_3d` """
        super().__init__()
        self._expand_id = '3D_blender'
        self._unkown_is_error = True

    def config(self, parent):
        super().config(parent)
        # Check we at least have a name for the source output
        if isinstance(self.pcb3d, type) or (isinstance(self.pcb3d, str) and not self.pcb3d):
            raise KiPlotConfigurationError('You must specify the name of the output that'
                                           ' generates the PCB3D file or its options')
        # Do we have outputs?
        if isinstance(self.outputs, type):
            self.outputs = []
        elif isinstance(self.outputs, BlenderOutputOptions):
            # One, make a list
            self.outputs = [self.outputs]
        # Ensure we have import options
        if isinstance(self.pcb_import, type):
            self.pcb_import = PCB2BlenderOptions()
        # Ensure we have a light
        if isinstance(self.light, type):
            # None
            if self.add_default_light:
                # Create one
                light = BlenderLightOptions()
                light.name = 'kibot_light'
                _, _, size = get_board_size()
                light.pos_x = -size*3.33
                light.pos_y = size*3.33
                light.pos_z = size*5.0
                self.light = [light]
            else:
                # The dark ...
                self.light = []
        elif isinstance(self.light, BlenderLightOptions):
            # Ensure a list
            self.light = [self.light]
        # Check light names
        light_names = set()
        for li in self.light:
            name = li.name if li.name else 'kibot_light'
            if name in light_names:
                id = 2
                while name+'_'+str(id) in light_names:
                    id += 1
                name = name+'_'+str(id)
            li.name = name
        # If no camera let the script create one
        if isinstance(self.camera, type):
            self.camera = None
        elif not self.camera.name:
            self.camera.name = 'kibot_camera'
        # Ensure we have some render options
        if isinstance(self.render_options, type):
            self.render_options = BlenderRenderOptions()
        # View point
        view = self._views.get(self.view, None)
        if view is not None:
            self.view = view
        self._expand_id += '_'+self._rviews.get(self.view)

    def get_output_filename(self, o, output_dir):
        if o.type == 'render':
            self._expand_ext = 'png'
        elif o.type == 'blender':
            self._expand_ext = 'blend'
        else:
            self._expand_ext = o.type
        return self._parent.expand_filename(output_dir, o.output)

    def get_targets(self, out_dir):
        return [self.get_output_filename(o, out_dir) for o in self.outputs]

    def create_vrml(self, dest_dir):
        tree = {'name': '_temporal_vrml_for_pcb3d',
                'type': 'vrml',
                'comment': 'Internally created for the PCB3D',
                'dir': dest_dir,
                'options': {'output': 'pcb.wrl',
                            'dir_models': 'components',
                            'use_pcb_center_as_ref': False,
                            'model_units': 'meters'}}
        out = RegOutput.get_class_for('vrml')()
        out.set_tree(tree)
        config_output(out)
        out.options.copy_options(self.pcb3d)
        logger.debug(' - Creating VRML ...')
        out.options.run(os.path.join(dest_dir, 'pcb.wrl'))

    def create_layers(self, dest_dir):
        out_dir = os.path.join(dest_dir, 'layers')
        tree = {'name': '_temporal_svgs_layers',
                'type': 'svg',
                'comment': 'Internally created for the PCB3D',
                'dir': out_dir,
                'options': {'output': '%i.%x',
                            'margin': 1,
                            'limit_viewbox': True,
                            'svg_precision': 6,
                            'drill_marks': 'none'},
                'layers': ['F.Cu', 'B.Cu', 'F.Paste', 'B.Paste', 'F.Mask', 'B.Mask',
                           {'layer': 'F.SilkS', 'suffix': 'F_SilkS'},
                           {'layer': 'B.SilkS', 'suffix': 'B_SilkS'}]}
        configure_and_run(tree, out_dir, ' - Creating SVG for layers ...')

    def create_pads(self, dest_dir):
        tree = {'name': '_temporal_pcb3d_tools',
                'type': 'pcb2blender_tools',
                'comment': 'Internally created for the PCB3D',
                'dir': dest_dir,
                'options': {'stackup_create': self.pcb3d.version == '2.1_haschtl'}}
        configure_and_run(tree, dest_dir, ' - Creating Pads and boundary ...')

    def create_pcb3d(self, data_dir):
        out_dir = self._parent.output_dir
        # Compute the name for the PCB3D
        cur_id = self._expand_id
        cur_ext = self._expand_ext
        self._expand_id = self.pcb3d._expand_id
        self._expand_ext = self.pcb3d._expand_ext
        out_name = self._parent.expand_filename(out_dir, self.pcb3d.output)
        self._expand_id = cur_id
        self._expand_ext = cur_ext
        tree = {'name': '_temporal_compress_pcb3d',
                'type': 'compress',
                'comment': 'Internally created for the PCB3D',
                'dir': out_dir,
                'options': {'output': out_name,
                            'format': 'ZIP',
                            'files': [{'source': os.path.join(data_dir, 'boards'),
                                       'dest': '/'},
                                      {'source': os.path.join(data_dir, 'boards/*'),
                                       'dest': 'boards'},
                                      {'source': os.path.join(data_dir, 'components'),
                                       'dest': '/'},
                                      {'source': os.path.join(data_dir, 'components/*'),
                                       'dest': 'components'},
                                      {'source': os.path.join(data_dir, 'layers'),
                                       'dest': '/'},
                                      {'source': os.path.join(data_dir, 'layers/*'),
                                       'dest': 'layers'},
                                      {'source': os.path.join(data_dir, 'pads'),
                                       'dest': '/'},
                                      {'source': os.path.join(data_dir, 'pads/*'),
                                       'dest': 'pads'},
                                      {'source': os.path.join(data_dir, 'pcb.wrl'),
                                       'dest': '/'},
                                      ]}}
        configure_and_run(tree, out_dir, ' - Creating the PCB3D ...')
        return out_name

    def solve_pcb3d(self):
        if isinstance(self.pcb3d, str):
            # An output creates it
            pcb3d_targets, _, pcb3d_out = get_output_targets(self.pcb3d, self._parent)
            pcb3d_file = pcb3d_targets[0]
            logger.debug('- From file '+pcb3d_file)
            if not pcb3d_out._done:
                logger.debug('-  Running '+self.pcb3d)
                run_output(pcb3d_out)
            self._pcb3d = PCB3DExportOptions()
            self._pcb3d.output = pcb3d_file
            # Needed by ensure tool
            self._pcb3d._parent = self._parent
        else:
            # We create it
            with TemporaryDirectory() as tmp_dir:
                # VRML
                self.create_vrml(tmp_dir)
                # SVG layers
                self.create_layers(tmp_dir)
                # Pads and bounds
                self.create_pads(tmp_dir)
                # Compress the files
                pcb3d_file = self.create_pcb3d(tmp_dir)
            self._pcb3d = self.pcb3d
            # Needed by ensure tool
            self.type = self._parent.type
        if not os.path.isfile(pcb3d_file):
            raise KiPlotConfigurationError('Missing '+pcb3d_file)
        return pcb3d_file

    def run(self, output):
        pcb3d_file = self.solve_pcb3d()
        # If no outputs specified just finish
        # Can be used to export the PCB to Blender
        if not self.outputs:
            return
        # Make sure Blender is available
        command = self._pcb3d.ensure_tool('Blender')
        # Create a JSON with the scene information
        with NamedTemporaryFile(mode='w', suffix='.json') as f:
            scene = {}
            if self.light:
                lights = [{'name': light.name, 'position': (light.pos_x, light.pos_y, light.pos_z)} for light in self.light]
                scene['lights'] = lights
            if self.camera:
                scene['camera'] = {'name': self.camera.name,
                                   'position': (self.camera.pos_x, self.camera.pos_y, self.camera.pos_z)}
            ro = self.render_options
            scene['render'] = {'samples': ro.samples,
                               'resolution_x': ro.resolution_x,
                               'resolution_y': ro.resolution_y,
                               'transparent_background': ro.transparent_background,
                               'background1': ro.background1,
                               'background2': ro.background2}
            if self.rotate_x:
                scene['rotate_x'] = -self.rotate_x
            if self.rotate_y:
                scene['rotate_y'] = -self.rotate_y
            if self.rotate_z:
                scene['rotate_z'] = -self.rotate_z
            if self.view:
                scene['view'] = self.view
            text = json.dumps(scene, sort_keys=True, indent=2)
            logger.debug('Scene:\n'+text)
            f.write(text)
            f.flush()
            # Create the command line
            script = os.path.join(os.path.dirname(__file__), 'blender_scripts', 'blender_export.py')
            cmd = [command, '-b', '--factory-startup', '-P', script, '--']
            pi = self.pcb_import
            if not pi.components:
                cmd.append('--no_components')
            if not pi.cut_boards:
                cmd.append('--dont_cut_boards')
            if pi.texture_dpi != 1016.0:
                cmd.extend(['--texture_dpi', str(pi.texture_dpi)])
            if not pi.center:
                cmd.append('--dont_center')
            if not pi.enhance_materials:
                cmd.append('--dont_enhance_materials')
            if not pi.merge_materials:
                cmd.append('--dont_merge_materials')
            if pi.solder_joints != "SMART":
                cmd.extend(['--solder_joints', pi.solder_joints])
            if not pi.stack_boards:
                cmd.append('--dont_stack_boards')
            cmd.append('--format')
            cmd.extend([o.type for o in self.outputs])
            cmd.append('--output')
            for o in self.outputs:
                cmd.append(self.get_output_filename(o, self._parent.output_dir))
            cmd.extend(['--scene', f.name])
            cmd.append(pcb3d_file)
            # Execute the command
            run_command(cmd)


@output_class
class Blender_Export(Base3D):
    """ Blender Export **Experimental**
        Exports the PCB in various 3D file formats.
        Also renders the PCB with high-quality.
        This output is complex to setup and needs very big dependencies.
        Please be patient when using it.
        You need Blender with the pcb2blender plug-in installed.
        Visit: [pcb2blender](https://github.com/30350n/pcb2blender).
        You can just generate the exported PCB if no output is specified.
        You can also export the PCB and render it at the same time """
    def __init__(self):
        super().__init__()
        with document:
            self.options = Blender_ExportOptions
            """ *[dict] Options for the `blender_export` output """
        self._category = 'PCB/3D'

    @staticmethod
    def get_conf_examples(name, layers, templates):
        if not GS.check_tool(name, 'Blender'):
            return None
        outs = []
        has_top = False
        has_bottom = False
        for la in layers:
            if la.is_top() or la.layer.startswith('F.'):
                has_top = True
            elif la.is_bottom() or la.layer.startswith('B.'):
                has_bottom = True
        if not has_top and not has_bottom:
            return None
        register_xmp_import('PCB2Blender_2_1')
        out_ops = {'pcb3d': '_PCB2Blender_2_1', 'outputs': [{'type': 'render'}, {'type': 'blender'}]}
        if has_top:
            gb = {}
            gb['name'] = 'basic_{}_top'.format(name)
            gb['comment'] = '3D view from top (Blender)'
            gb['type'] = name
            gb['dir'] = '3D'
            gb['options'] = copy(out_ops)
            outs.append(gb)
            gb = {}
            gb['name'] = 'basic_{}_30deg'.format(name)
            gb['comment'] = '3D view from 30 degrees (Blender)'
            gb['type'] = name
            gb['dir'] = '3D'
            gb['output_id'] = '_30deg'
            gb['options'] = copy(out_ops)
            gb['options'].update({'rotate_x': 30, 'rotate_z': -20})
            outs.append(gb)
        if has_bottom:
            gb = {}
            gb['name'] = 'basic_{}_bottom'.format(name)
            gb['comment'] = '3D view from bottom (Blender)'
            gb['type'] = name
            gb['dir'] = '3D'
            gb['options'] = copy(out_ops)
            gb['options'].update({'view': 'bottom'})
            outs.append(gb)
        return outs
