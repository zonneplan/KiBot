"""
Main Kiplot code
"""

from datetime import datetime
import os
from sys import exit
import operator
from shutil import which
from glob import glob
from subprocess import (call, run, PIPE, check_output, CalledProcessError,
                        STDOUT)
import logging
from distutils.version import StrictVersion
import re

from . import plot_config as PCfg
from . import error
from . import log
from . import misc

logger = log.get_logger(__name__)

try:
    import pcbnew
    from pcbnew import GERBER_JOBFILE_WRITER
except ImportError:  # pragma: no cover
    log.init(False, False)
    logger.error("Failed to import pcbnew Python module."
                 " Is KiCad installed?"
                 " Do you need to add it to PYTHONPATH?")
    exit(misc.NO_PCBNEW_MODULE)


class PlotError(error.KiPlotError):

    pass


def plot_error(msg):
    logger.error(msg)
    exit(misc.PLOT_ERROR)


def level_debug():
    """ Determine if we are in debug mode """
    return logger.getEffectiveLevel() <= logging.DEBUG


def check_version(command, version):
    cmd = [command, '--version']
    logger.debug('Running: '+str(cmd))
    result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    z = re.match(command + r' (\d+\.\d+\.\d+)', result.stdout)
    if not z:
        logger.error('Unable to determine ' + command + ' version:\n' +
                     result.stdout)
        exit(misc.MISSING_TOOL)
    res = z.groups()
    if StrictVersion(res[0]) < StrictVersion(version):
        logger.error('Wrong version for `'+command+'` ('+res[0]+'), must be ' +
                     version+' or newer.')
        exit(misc.MISSING_TOOL)


def check_script(cmd, url, version=None):
    if which(cmd) is None:
        logger.error('No `'+cmd+'` command found.\n'
                     'Please install it, visit: '+url)
        exit(misc.MISSING_TOOL)
    if version is not None:
        check_version(cmd, version)


def check_eeschema_do(file):
    check_script(misc.CMD_EESCHEMA_DO, misc.URL_EESCHEMA_DO, '1.4.0')
    sch_file = os.path.splitext(file)[0] + '.sch'
    if not os.path.isfile(sch_file):
        logger.error('Missing schematic file: ' + sch_file)
        exit(misc.NO_SCH_FILE)
    return sch_file


class Plotter(object):
    """
    Main Plotter class - this is what will perform the plotting
    """

    def __init__(self, cfg):
        self.cfg = cfg

    def plot(self, brd_file, target, invert, skip_pre):

        logger.debug("Starting plot of board {}".format(brd_file))
        self._preflight_checks(brd_file, skip_pre)

        n = len(target)
        if n == 0 and invert:
            # Skip all targets
            logger.debug('Skipping all outputs')
            return

        board = None
        for op in self.cfg.outputs:

            if (n == 0) or ((op.name in target) ^ invert):
                logger.info('- %s (%s) [%s]' % (op.description, op.name, op.options.type))

                output_dir = self._get_output_dir(op)
                if (not self._output_is_schematic(op)) and (board is None):
                    board = self._load_board(brd_file)

                try:
                    if self._output_is_layer(op):
                        self._do_layer_plot(board, output_dir, op, brd_file)
                    elif self._output_is_drill(op):
                        self._do_drill_plot(board, output_dir, op)
                    elif self._output_is_position(op):
                        self._do_position_plot(board, output_dir, op)
                    elif self._output_is_bom(op):
                        self._do_bom(output_dir, op, brd_file)
                    elif self._output_is_sch_print(op):
                        self._do_sch_print(output_dir, op, brd_file)
                    elif self._output_is_pcb_print(op):
                        self._do_pcb_print(board, output_dir, op, brd_file)
                    elif self._output_is_step(op):
                        self._do_step(output_dir, op, brd_file)
                    else:  # pragma no cover
                        # We shouldn't get here, means the above if is incomplete
                        plot_error("Don't know how to plot type "+op.options.type)
                except PlotError as e:
                    plot_error("In section '"+op.name+"' ("+op.options.type+"): "+str(e))
            else:
                logger.debug('Skipping %s output', op.name)

    def _load_board(self, brd_file):
        try:
            board = pcbnew.LoadBoard(brd_file)
            if self.cfg.check_zone_fills:
                pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        except OSError as e:
            logger.error('Error loading PCB file. Currupted?')
            logger.error(e)
            exit(misc.CORRUPTED_PCB)
        assert board is not None
        logger.debug("Board loaded")
        return board

    def _preflight_checks(self, brd_file, skip_pre):
        logger.debug("Preflight checks")

        if skip_pre is not None:
            if skip_pre[0] == 'all':
                logger.debug("Skipping all pre-flight actions")
                return
            else:
                skip_list = skip_pre[0].split(',')
                for skip in skip_list:
                    if skip == 'all':
                        logger.error('All can\'t be part of a list of actions '
                                     'to skip. Use `--skip all`')
                        exit(misc.EXIT_BAD_ARGS)
                    elif skip == 'run_drc':
                        self.cfg.run_drc = False
                        logger.debug('Skipping run_drc')
                    elif skip == 'update_xml':
                        self.cfg.update_xml = False
                        logger.debug('Skipping update_xml')
                    elif skip == 'run_erc':
                        self.cfg.run_erc = False
                        logger.debug('Skipping run_erc')
                    elif skip == 'check_zone_fills':
                        self.cfg.check_zone_fills = False
                        logger.debug('Skipping run_erc')
                    else:
                        logger.error('Unknown action to skip: '+skip)
                        exit(misc.EXIT_BAD_ARGS)
        # Create the filters file
        filter_file = None
        if (self.cfg.run_erc or self.cfg.run_drc) and self.cfg.filters:
            filter_file = os.path.join(self.cfg.outdir, 'kiplot_errors.filter')
            with open(filter_file, 'w') as f:
                f.write(self.cfg.filters)
        if self.cfg.run_erc:
            self._run_erc(brd_file, filter_file)
        if self.cfg.update_xml:
            self._update_xml(brd_file)
        if self.cfg.run_drc:
            self._run_drc(brd_file, self.cfg.ignore_unconnected, filter_file)

    def _run_erc(self, brd_file, filter_file):
        sch_file = check_eeschema_do(brd_file)
        cmd = [misc.CMD_EESCHEMA_DO, 'run_erc']
        if filter_file:
            cmd.extend(['-f', filter_file])
        cmd.extend([sch_file, self.cfg.outdir])
        # If we are in verbose mode enable debug in the child
        if level_debug():
            cmd.insert(1, '-vv')
            cmd.insert(1, '-r')
        logger.info('- Running the ERC')
        logger.debug('Executing: '+str(cmd))
        ret = call(cmd)
        if ret:
            if ret < 0:
                logger.error('ERC errors: %d', -ret)
            else:
                logger.error('ERC returned %d', ret)
            exit(misc.ERC_ERROR)

    def _update_xml(self, brd_file):
        sch_file = check_eeschema_do(brd_file)
        cmd = [misc.CMD_EESCHEMA_DO, 'bom_xml', sch_file, self.cfg.outdir]
        # If we are in verbose mode enable debug in the child
        if level_debug():
            cmd.insert(1, '-vv')
            cmd.insert(1, '-r')
        logger.info('- Updating BoM in XML format')
        logger.debug('Executing: '+str(cmd))
        ret = call(cmd)
        if ret:
            logger.error('Failed to update the BoM, error %d', ret)
            exit(misc.BOM_ERROR)

    def _run_drc(self, brd_file, ignore_unconnected, filter_file):
        check_script(misc.CMD_PCBNEW_RUN_DRC, misc.URL_PCBNEW_RUN_DRC, '1.4.0')
        cmd = [misc.CMD_PCBNEW_RUN_DRC, 'run_drc']
        if filter_file:
            cmd.extend(['-f', filter_file])
        cmd.extend([brd_file, self.cfg.outdir])
        # If we are in verbose mode enable debug in the child
        if level_debug():
            cmd.insert(1, '-vv')
            cmd.insert(1, '-r')
        if ignore_unconnected:
            cmd.insert(1, '-i')
        logger.info('- Running the DRC')
        logger.debug('Executing: '+str(cmd))
        ret = call(cmd)
        if ret:
            if ret < 0:
                logger.error('DRC errors: %d', -ret)
            else:
                logger.error('DRC returned %d', ret)
            exit(misc.DRC_ERROR)

    def _output_is_layer(self, output):
        """ All the formats for 'PCB|Plot' """
        return output.options.type in [
            PCfg.OutputOptions.GERBER,
            PCfg.OutputOptions.POSTSCRIPT,
            PCfg.OutputOptions.DXF,
            PCfg.OutputOptions.SVG,
            PCfg.OutputOptions.PDF,
            PCfg.OutputOptions.HPGL,
        ]

    def _output_is_drill(self, output):
        """ All the drill formats' """
        return output.options.type in [
            PCfg.OutputOptions.EXCELLON,
            PCfg.OutputOptions.GERB_DRILL,
        ]

    def _output_is_position(self, output):
        return output.options.type == PCfg.OutputOptions.POSITION

    def _output_is_sch_print(self, output):
        return output.options.type == PCfg.OutputOptions.PDF_SCH_PRINT

    def _output_is_pcb_print(self, output):
        return output.options.type == PCfg.OutputOptions.PDF_PCB_PRINT

    def _output_is_step(self, output):
        return output.options.type == PCfg.OutputOptions.STEP

    def _output_is_bom(self, output):
        return output.options.type in [
            PCfg.OutputOptions.KIBOM,
            PCfg.OutputOptions.IBOM,
        ]

    def _output_is_schematic(self, output):
        """ All the outputs involving the SCH and not the PCB """
        return self._output_is_bom(output) or self._output_is_sch_print(output)

    def _get_layer_plot_format(self, output):
        """
        Gets the Pcbnew plot format for a given KiPlot output type
        """

        mapping = {
            PCfg.OutputOptions.GERBER: pcbnew.PLOT_FORMAT_GERBER,
            PCfg.OutputOptions.POSTSCRIPT: pcbnew.PLOT_FORMAT_POST,
            PCfg.OutputOptions.HPGL: pcbnew.PLOT_FORMAT_HPGL,
            PCfg.OutputOptions.PDF: pcbnew.PLOT_FORMAT_PDF,
            PCfg.OutputOptions.DXF: pcbnew.PLOT_FORMAT_DXF,
            PCfg.OutputOptions.SVG: pcbnew.PLOT_FORMAT_SVG,
        }

        try:
            return mapping[output.options.type]
        except KeyError:
            pass

        raise ValueError("Don't know how to translate plot type: {}"
                         .format(output.options.type))

    def _do_layer_plot(self, board, output_dir, output, file_name):

        # fresh plot controller
        plot_ctrl = pcbnew.PLOT_CONTROLLER(board)
        # set up plot options for the whole output
        self._configure_plot_ctrl(plot_ctrl, output, output_dir)

        po = plot_ctrl.GetPlotOptions()
        layer_cnt = board.GetCopperLayerCount()

        # Gerber Job files aren't automagically created
        # We need to assist KiCad
        create_job = po.GetCreateGerberJobFile()
        if create_job:
            jobfile_writer = GERBER_JOBFILE_WRITER(board)

        plot_ctrl.SetColorMode(True)

        # plot every layer in the output
        for l in output.layers:

            layer = l.layer
            suffix = l.suffix
            desc = l.desc

            # for inner layers, we can now check if the layer exists
            if layer.is_inner:
                if layer.layer < 1 or layer.layer >= layer_cnt - 1:
                    raise PlotError(
                            "Inner layer {} is not valid for this board"
                            .format(layer.layer))

            # Set current layer
            plot_ctrl.SetLayer(layer.layer)

            # Skipping NPTH is controlled by whether or not this is
            # a copper layer
            is_cu = pcbnew.IsCopperLayer(layer.layer)
            po.SetSkipPlotNPTH_Pads(is_cu)

            plot_format = self._get_layer_plot_format(output)

            # Plot single layer to file
            logger.debug("Opening plot file for layer {} ({}) {} {}"
                         .format(layer.layer, suffix, plot_format, desc))
            if not plot_ctrl.OpenPlotfile(suffix, plot_format, desc):
                plot_error("OpenPlotfile failed!")

            logger.debug("Plotting layer {} to {}".format(
                layer.layer, plot_ctrl.GetPlotFileName()))
            plot_ctrl.PlotLayer()
            plot_ctrl.ClosePlot()
            if create_job:
                jobfile_writer.AddGbrFile(layer.layer, os.path.basename(
                                          plot_ctrl.GetPlotFileName()))

        if create_job:
            base_fn = os.path.join(
                         os.path.dirname(plot_ctrl.GetPlotFileName()),
                         os.path.basename(file_name))
            base_fn = os.path.splitext(base_fn)[0]
            job_fn = base_fn+'-job.gbrjob'
            jobfile_writer.CreateJobFile(job_fn)

    def _configure_excellon_drill_writer(self, board, offset, options):

        drill_writer = pcbnew.EXCELLON_WRITER(board)

        to = options.type_options

        mirror_y = to.mirror_y_axis
        minimal_header = to.minimal_header

        merge_npth = to.pth_and_npth_single_file
        zeros_format = pcbnew.EXCELLON_WRITER.DECIMAL_FORMAT

        drill_writer.SetOptions(mirror_y, minimal_header, offset, merge_npth)
        drill_writer.SetFormat(to.metric_units, zeros_format)

        return drill_writer

    def _configure_gerber_drill_writer(self, board, offset, options):

        drill_writer = pcbnew.GERBER_WRITER(board)

        # hard coded in UI?
        drill_writer.SetFormat(5)
        drill_writer.SetOptions(offset)

        return drill_writer

    def _do_drill_plot(self, board, output_dir, output):

        to = output.options.type_options

        # dialog_gendrill.cpp:357
        if to.use_aux_axis_as_origin:
            offset = board.GetAuxOrigin()
        else:
            offset = pcbnew.wxPoint(0, 0)

        if output.options.type == PCfg.OutputOptions.EXCELLON:
            drill_writer = self._configure_excellon_drill_writer(
                board, offset, output.options)
        elif output.options.type == PCfg.OutputOptions.GERB_DRILL:
            drill_writer = self._configure_gerber_drill_writer(
                board, offset, output.options)
        else:
            plot_error("Can't make a writer for type "+output.options.type)

        gen_drill = True
        gen_map = to.generate_map
        gen_report = to.generate_report

        if gen_drill:
            logger.debug("Generating drill files in "+output_dir)

        if gen_map:
            drill_writer.SetMapFileFormat(to.map_options.type)
            logger.debug("Generating drill map type {} in {}"
                         .format(to.map_options.type, output_dir))

        drill_writer.CreateDrillandMapFilesSet(output_dir, gen_drill, gen_map)

        if gen_report:
            drill_report_file = os.path.join(output_dir,
                                             to.report_options.filename)
            logger.debug("Generating drill report: "+drill_report_file)

            drill_writer.GenDrillReportFile(drill_report_file)

    def _do_position_plot_ascii(self, board, output_dir, output, columns,
                                modulesStr, maxSizes):
        to = output.options.type_options
        name = os.path.splitext(os.path.basename(board.GetFileName()))[0]

        topf = None
        botf = None
        bothf = None
        if to.separate_files_for_front_and_back:
            topf = open(os.path.join(output_dir, "{}-top.pos".format(name)), 'w')
            botf = open(os.path.join(output_dir, "{}-bottom.pos".format(name)),
                        'w')
        else:
            bothf = open(os.path.join(output_dir, "{}-both.pos").format(name), 'w')

        files = [f for f in [topf, botf, bothf] if f is not None]
        for f in files:
            f.write('### Module positions - created on {} ###\n'.format(
                datetime.now().strftime("%a %d %b %Y %X %Z")
            ))
            f.write('### Printed by KiPlot\n')
            unit = {'millimeters': 'mm',
                    'inches': 'in'}[to.units]
            f.write('## Unit = {}, Angle = deg.\n'.format(unit))

        if topf is not None:
            topf.write('## Side : top\n')
        if botf is not None:
            botf.write('## Side : bottom\n')
        if bothf is not None:
            bothf.write('## Side : both\n')

        for f in files:
            f.write('# ')
            for idx, col in enumerate(columns):
                if idx > 0:
                    f.write("   ")
                f.write("{0: <{width}}".format(col, width=maxSizes[idx]))
            f.write('\n')

        # Account for the "# " at the start of the comment column
        maxSizes[0] = maxSizes[0] + 2

        for m in modulesStr:
            fle = bothf
            if fle is None:
                if m[-1] == "top":
                    fle = topf
                else:
                    fle = botf
            for idx, col in enumerate(m):
                if idx > 0:
                    fle.write("   ")
                fle.write("{0: <{width}}".format(col, width=maxSizes[idx]))
            fle.write("\n")

        for f in files:
            f.write("## End\n")

        if topf is not None:
            topf.close()
        if botf is not None:
            botf.close()
        if bothf is not None:
            bothf.close()

    def _do_position_plot_csv(self, board, output_dir, output, columns,
                              modulesStr):
        to = output.options.type_options
        name = os.path.splitext(os.path.basename(board.GetFileName()))[0]

        topf = None
        botf = None
        bothf = None
        if to.separate_files_for_front_and_back:
            topf = open(os.path.join(output_dir, "{}-top-pos.csv".format(name)),
                        'w')
            botf = open(os.path.join(output_dir, "{}-bottom-pos.csv".format(name)),
                        'w')
        else:
            bothf = open(os.path.join(output_dir, "{}-both-pos.csv").format(name),
                         'w')

        files = [f for f in [topf, botf, bothf] if f is not None]

        for f in files:
            f.write(",".join(columns))
            f.write("\n")

        for m in modulesStr:
            fle = bothf
            if fle is None:
                if m[-1] == "top":
                    fle = topf
                else:
                    fle = botf
            fle.write(",".join('"{}"'.format(e) for e in m))
            fle.write("\n")

        if topf is not None:
            topf.close()
        if botf is not None:
            botf.close()
        if bothf is not None:
            bothf.close()

    def _do_position_plot(self, board, output_dir, output):
        to = output.options.type_options

        columns = ["Ref", "Val", "Package", "PosX", "PosY", "Rot", "Side"]
        colcount = len(columns)

        # Note: the parser already checked the units are milimeters or inches
        conv = 1.0
        if to.units == 'millimeters':
            conv = 1.0 / pcbnew.IU_PER_MM
        else:  # to.units == 'inches':
            conv = 0.001 / pcbnew.IU_PER_MILS

        # Format all strings
        modules = []
        for m in sorted(board.GetModules(),
                        key=operator.methodcaller('GetReference')):
            if (to.only_smd and m.GetAttributes() == 1) or not to.only_smd:
                center = m.GetCenter()
                # See PLACE_FILE_EXPORTER::GenPositionData() in
                # export_footprints_placefile.cpp for C++ version of this.
                modules.append([
                    "{}".format(m.GetReference()),
                    "{}".format(m.GetValue()),
                    "{}".format(m.GetFPID().GetLibItemName()),
                    "{:.4f}".format(center.x * conv),
                    "{:.4f}".format(-center.y * conv),
                    "{:.4f}".format(m.GetOrientationDegrees()),
                    "{}".format("bottom" if m.IsFlipped() else "top")
                ])

        # Find max width for all columns
        maxlengths = [0] * colcount
        for row in range(len(modules)):
            for col in range(colcount):
                maxlengths[col] = max(maxlengths[col], len(modules[row][col]))

        # Note: the parser already checked the format is ASCII or CSV
        if to.format.lower() == 'ascii':
            self._do_position_plot_ascii(board, output_dir, output, columns,
                                         modules, maxlengths)
        else:  # if to.format.lower() == 'csv':
            self._do_position_plot_csv(board, output_dir, output, columns,
                                       modules)

    def _do_sch_print(self, output_dir, output, brd_file):
        sch_file = check_eeschema_do(brd_file)
        cmd = [misc.CMD_EESCHEMA_DO, 'export', '--all_pages',
               '--file_format', 'pdf', sch_file, output_dir]
        if level_debug():
            cmd.insert(1, '-vv')
            cmd.insert(1, '-r')
        logger.debug('Executing: '+str(cmd))
        ret = call(cmd)
        if ret:
            logger.error(misc.CMD_EESCHEMA_DO+' returned %d', ret)
            exit(misc.PDF_SCH_PRINT)
        to = output.options.type_options
        if to.output:
            cur = os.path.abspath(os.path.join(output_dir, os.path.splitext(os.path.basename(brd_file))[0]) + '.pdf')
            new = os.path.abspath(os.path.join(output_dir, to.output))
            logger.debug('Moving '+cur+' -> '+new)
            os.rename(cur, new)

    def _do_step(self, output_dir, op, brd_file):
        to = op.options.type_options
        # Output file name
        output = to.output
        if output is None:
            output = os.path.splitext(os.path.basename(brd_file))[0]+'.step'
        output = os.path.abspath(os.path.join(output_dir, output))
        # Make units explicit
        if to.metric_units:
            units = 'mm'
        else:
            units = 'in'
        # Base command with overwrite
        cmd = [misc.KICAD2STEP, '-o', output, '-f']
        # Add user options
        if to.no_virtual:
            cmd.append('--no-virtual')
        if to.min_distance is not None:
            cmd.append('--min-distance="{}{}"'.format(to.min_distance, units))
        if to.origin == 'drill':
            cmd.append('--drill-origin')
        elif to.origin == 'grid':
            cmd.append('--grid-origin')
        else:
            to.origin.replace(',', 'x')
            cmd.append('--user-origin="{}{}"'.format(to.origin, units))
        # The board
        cmd.append(brd_file)
        # Execute and inform is successful
        logger.debug('Executing: '+str(cmd))
        try:
            cmd_output = check_output(cmd, stderr=STDOUT)
        except CalledProcessError as e: # pragma: no cover
            # Current kicad2step always returns 0!!!!
            # This is why I'm excluding it from coverage
            logger.error('Failed to create Step file, error %d', e.returncode)
            if e.output:
                logger.debug('Output from command: '+e.output.decode())
            exit(misc.KICAD2STEP_ERR)
        logger.debug('Output from command:\n'+cmd_output.decode())

    def _do_pcb_print(self, board, output_dir, output, brd_file):
        check_script(misc.CMD_PCBNEW_PRINT_LAYERS,
                     misc.URL_PCBNEW_PRINT_LAYERS, '1.4.1')
        to = output.options.type_options
        # Verify the inner layers
        layer_cnt = board.GetCopperLayerCount()
        for l in output.layers:
            layer = l.layer
            # for inner layers, we can now check if the layer exists
            if layer.is_inner:
                if layer.layer < 1 or layer.layer >= layer_cnt - 1:
                    raise PlotError(
                            "Inner layer {} is not valid for this board"
                            .format(layer.layer))
        cmd = [misc.CMD_PCBNEW_PRINT_LAYERS, 'export',
               '--output_name', to.output_name]
        if self.cfg.check_zone_fills:
            cmd.append('-f')
        cmd.extend([brd_file, output_dir])
        if level_debug():
            cmd.insert(1, '-vv')
            cmd.insert(1, '-r')
        # Add the layers
        for l in output.layers:
            cmd.append(l.layer.name)
        logger.debug('Executing: '+str(cmd))
        ret = call(cmd)
        if ret:
            logger.error(misc.CMD_PCBNEW_PRINT_LAYERS+' returned %d', ret)
            exit(misc.PDF_PCB_PRINT)

    def _do_bom(self, output_dir, output, brd_file):
        if output.options.type == 'kibom':
            self._do_kibom(output_dir, output, brd_file)
        else:
            self._do_ibom(output_dir, output, brd_file)

    def _do_kibom(self, output_dir, output, brd_file):
        check_script(misc.CMD_KIBOM, misc.URL_KIBOM)
        to = output.options.type_options
        format = to.format.lower()
        prj = os.path.splitext(os.path.relpath(brd_file))[0]
        logger.debug('Doing BoM, format '+format+' prj: '+prj)
        cmd = [misc.CMD_KIBOM, prj+'.xml',
               os.path.join(output_dir, os.path.basename(prj))+'.'+format]
        logger.debug('Running: '+str(cmd))
        try:
            cmd_output = check_output(cmd, stderr=STDOUT)
        except CalledProcessError as e:
            logger.error('Failed to create BoM, error %d', e.returncode)
            if e.output:
                logger.debug('Output from command: '+e.output.decode())
            exit(misc.BOM_ERROR)
        for f in glob(os.path.join(output_dir, prj)+'*.tmp'):
            os.remove(f)
        logger.debug('Output from command:\n'+cmd_output.decode())

    def _do_ibom(self, output_dir, output, brd_file):
        check_script(misc.CMD_IBOM, misc.URL_IBOM)
        prj = os.path.splitext(os.path.relpath(brd_file))[0]
        logger.debug('Doing Interactive BoM, prj: '+prj)
        cmd = [misc.CMD_IBOM, brd_file,
               '--dest-dir', output_dir,
               '--no-browser', ]
        to = output.options.type_options
        if to.blacklist:
            cmd.append('--blacklist')
            cmd.append(to.blacklist)
        if to.name_format:
            cmd.append('--name-format')
            cmd.append(to.name_format)
        logger.debug('Running: '+str(cmd))
        try:
            cmd_output = check_output(cmd, stderr=STDOUT)
        except CalledProcessError as e:
            logger.error('Failed to create BoM, error %d', e.returncode)
            if e.output:
                logger.debug('Output from command: '+e.output.decode())
            exit(misc.BOM_ERROR)
        logger.debug('Output from command:\n'+cmd_output.decode()+'\n')

    def _configure_gerber_opts(self, po, output):

        # true if gerber
        po.SetUseGerberAttributes(True)

        assert(output.options.type == PCfg.OutputOptions.GERBER)
        gerb_opts = output.options.type_options

        po.SetSubtractMaskFromSilk(gerb_opts.subtract_mask_from_silk)
        po.SetUseGerberProtelExtensions(gerb_opts.use_protel_extensions)
        po.SetGerberPrecision(gerb_opts.gerber_precision)
        po.SetCreateGerberJobFile(gerb_opts.create_gerber_job_file)

        po.SetUseGerberAttributes(gerb_opts.use_gerber_x2_attributes)
        po.SetIncludeGerberNetlistInfo(gerb_opts.use_gerber_net_attributes)

    def _configure_hpgl_opts(self, po, output):

        assert(output.options.type == PCfg.OutputOptions.HPGL)
        hpgl_opts = output.options.type_options

        po.SetHPGLPenDiameter(hpgl_opts.pen_width)

    def _configure_ps_opts(self, po, output):

        assert(output.options.type == PCfg.OutputOptions.POSTSCRIPT)
        ps_opts = output.options.type_options

        po.SetWidthAdjust(ps_opts.width_adjust)
        po.SetFineScaleAdjustX(ps_opts.scale_adjust_x)
        po.SetFineScaleAdjustX(ps_opts.scale_adjust_y)
        po.SetA4Output(ps_opts.a4_output)

    def _configure_dxf_opts(self, po, output):

        assert(output.options.type == PCfg.OutputOptions.DXF)
        dxf_opts = output.options.type_options

        po.SetDXFPlotPolygonMode(dxf_opts.polygon_mode)

    def _get_output_dir(self, output):

        # outdir is a combination of the config and output
        outdir = os.path.join(self.cfg.outdir, output.outdir)

        logger.debug("Output destination: {}".format(outdir))
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        return outdir

    def _configure_plot_ctrl(self, plot_ctrl, output, output_dir):

        logger.debug("Configuring plot controller for output")

        po = plot_ctrl.GetPlotOptions()
        po.SetOutputDirectory(output_dir)

        opts = output.options.type_options

        po.SetLineWidth(opts.line_width)

        po.SetAutoScale(opts.auto_scale)
        po.SetScale(opts.scaling)

        po.SetMirror(opts.mirror_plot)
        po.SetNegative(opts.negative_plot)

        po.SetPlotFrameRef(opts.plot_sheet_reference)
        po.SetPlotReference(opts.plot_footprint_refs)
        po.SetPlotValue(opts.plot_footprint_values)
        po.SetPlotInvisibleText(opts.force_plot_invisible_refs_vals)

        po.SetExcludeEdgeLayer(opts.exclude_edge_layer)
        po.SetPlotPadsOnSilkLayer(not opts.exclude_pads_from_silkscreen)
        po.SetUseAuxOrigin(opts.use_aux_axis_as_origin)

        po.SetPlotViaOnMaskLayer(not opts.tent_vias)

        # in general, false, but gerber will set it back later
        po.SetUseGerberAttributes(False)
        # Only useful for gerber outputs
        po.SetCreateGerberJobFile(False)

        if output.options.type == PCfg.OutputOptions.GERBER:
            self._configure_gerber_opts(po, output)
        elif output.options.type == PCfg.OutputOptions.POSTSCRIPT:
            self._configure_ps_opts(po, output)
        elif output.options.type == PCfg.OutputOptions.DXF:
            self._configure_dxf_opts(po, output)
        elif output.options.type == PCfg.OutputOptions.HPGL:
            self._configure_hpgl_opts(po, output)

        po.SetDrillMarksType(opts.drill_marks)

        # We'll come back to this on a per-layer basis
        po.SetSkipPlotNPTH_Pads(False)
