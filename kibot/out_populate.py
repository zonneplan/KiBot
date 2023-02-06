# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Salvador E. Tropea
# Copyright (c) 2022-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - name: mistune
    python_module: true
    debian: python3-mistune
    arch: python-mistune
    role: mandatory
"""
import os
from tempfile import NamedTemporaryFile
# Here we import the whole module to make monkeypatch work
from .error import KiPlotConfigurationError
from .misc import W_PCBDRAW, RENDERERS
from .gs import GS
from .kiplot import config_output, run_output
from .optionable import Optionable
from .out_base import VariantOptions
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log


logger = log.get_logger()


def pcbdraw_warnings(tag, msg):
    logger.warning('{}({}) {}'.format(W_PCBDRAW, tag, msg))


def _get_tmp_name(ext):
    with NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
        f.close()
    return f.name


class PopulateOptions(VariantOptions):
    def __init__(self):
        with document:
            self.renderer = ''
            """ *Name of the output used to render the PCB steps.
                Currently this must be a `pcbdraw` or `render_3d` output """
            self.template = 'simple'
            """ [string] The name of the handlebars template used for the HTML output.
                The extension must be `.handlebars`, it will be added when missing.
                The `simple.handlebars` template is a built-in template """
            self.format = 'html'
            """ *[html,md] Format for the generated output """
            self.initial_components = Optionable
            """ [string|list(string)=''] List of components soldered before the first step """
            self.input = ''
            """ *Name of the input file describing the assembly. Must be a markdown file.
                Note that the YAML section of the file will be skipped, all the needed information
                comes from this output and the `renderer` output """
            self.imgname = 'img/populating_%d.%x'
            """ Pattern used for the image names. The `%d` is replaced by the image number.
                The `%x` is replaced by the extension. Note that the format is selected by the
                `renderer` """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        # Validate the input file name
        if not self.input:
            raise KiPlotConfigurationError('You must specify an input markdown file')
        if not os.path.isfile(self.input):
            raise KiPlotConfigurationError('Missing input file `{}`'.format(self.input))
        # Initial components
        self.initial_components = Optionable.force_list(self.initial_components)
        # Validate the image patter name
        if '%d' not in self.imgname:
            raise KiPlotConfigurationError('The image pattern must contain `%d` `{}`'.format(self.imgname))

    def get_out_file_name(self):
        return 'index.html' if self.format == 'html' else 'index.md'

    def get_targets(self, out_dir):
        img_dir = os.path.dirname(self._parent.expand_filename(out_dir, self.imgname))
        return [self._parent.expand_filename(out_dir, self.get_out_file_name()), img_dir]

    def generate_image(self, side, components, active_components, name, options):
        logger.debug('Starting renderer with side: {}, components: {}, high: {}, image: {}'.
                     format(side, components, active_components, name))
        # Configure it according to our needs
        o_name = options.setup_renderer(components, active_components, side.startswith("back"), name)
        self._renderer.dir = self._parent.dir
        self._renderer._done = False
        run_output(self._renderer)
        return o_name

    def generate_images(self, dir_name, content):
        options = self._renderer.get_renderer_options()
        if options is None:
            raise KiPlotConfigurationError('No suitable renderer ({})'.format(self._renderer))
        # Memorize the current options
        options.save_renderer_options()
        dir = os.path.dirname(os.path.join(dir_name, self.imgname))
        if not os.path.exists(dir):
            os.makedirs(dir)
        counter = 0
        for item in content:
            if item["type"] != "steps":
                continue
            for x in item["steps"]:
                counter += 1
                filename = self.imgname.replace('%d', str(counter))
                x["img"] = self.generate_image(x["side"], x["components"], x["active_components"], filename, options)
        # Restore the options
        options.restore_renderer_options()
        return content

    def run(self, dir_name):
        # Ensure we have mistune
        self.ensure_tool('mistune')
        # Now we can use populate
        from .PcbDraw.populate import (load_content, get_data_path, read_template, create_renderer, parse_content,
                                       generate_html, generate_markdown, find_data_file)

        is_html = self.format == 'html'
        # Check the renderer output is valid
        out = RegOutput.get_output(self.renderer)
        if out is None:
            raise KiPlotConfigurationError('Unknown output `{}` selected in {}'.format(self.renderer, self._parent))
        config_output(out)
        if out.type not in RENDERERS:
            raise KiPlotConfigurationError('The `renderer` must be {} type, not {}'.format(RENDERERS, out.type))
        self._renderer = out
        # Load the input content
        try:
            _, content = load_content(self.input)
        except IOError:
            raise KiPlotConfigurationError('Failed to load `{}`'.format(self.input))
        # Load the template
        if self.format == 'html':
            data_path = get_data_path()
            data_path.insert(0, os.path.join(GS.get_resource_path('pcbdraw'), 'templates'))
            template_file = find_data_file(self.template, '.handlebars', data_path)
            if not template_file:
                raise KiPlotConfigurationError('Unable to find template file `{}`'.format(self.template))
            try:
                self._template = read_template(template_file)
            except IOError:
                raise KiPlotConfigurationError('Failed to load file `{}`'.format(template_file))
        # Initialize the output file renderer
        renderer = create_renderer(self.format, self.initial_components)
        outputfile = self.get_out_file_name()
        # Parse the input markdown
        parsed_content = parse_content(renderer, content)
        logger.debugl(3, parsed_content)
        # Generate the images
        self.generate_images(dir_name, parsed_content)
        # Generate the output file content
        if is_html:
            output_content = generate_html(self._template, parsed_content)
        else:
            output_content = generate_markdown(parsed_content)
        logger.debugl(3, output_content)
        # Write it to the output file
        with open(os.path.join(dir_name, outputfile), "wb") as f:
            f.write(output_content)


@output_class
class Populate(BaseOutput):  # noqa: F821
    """ Populate - Assembly instructions builder
        Creates a markdown and/or HTML file explaining how to assembly a PCB.
        Each step shows the already soldered components and the ones to add highlighted.
        This is equivalent to the PcbDraw's Populate command, but integrated to KiBot.
        For more information about the input markdown file please consult the
        [documentation](docs/populate.md) """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PopulateOptions
            """ *[dict] Options for the `populate` output """
        self._category = 'PCB/docs'
