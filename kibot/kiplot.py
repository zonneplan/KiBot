# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
"""
Main KiBot code
"""

import os
import re
from sys import exit
from sys import path as sys_path
import shlex
from shutil import which
from subprocess import run, PIPE, STDOUT, Popen, CalledProcessError
from glob import glob
from importlib.util import spec_from_file_location, module_from_spec
from collections import OrderedDict

from .gs import GS
from .registrable import RegOutput
from .misc import (PLOT_ERROR, CORRUPTED_PCB, EXIT_BAD_ARGS, CORRUPTED_SCH, version_str2tuple,
                   EXIT_BAD_CONFIG, WRONG_INSTALL, UI_SMD, UI_VIRTUAL, TRY_INSTALL_CHECK, MOD_SMD, MOD_THROUGH_HOLE,
                   MOD_VIRTUAL, W_PCBNOSCH, W_NONEEDSKIP, W_WRONGCHAR, name2make, W_TIMEOUT, W_KIAUTO, W_VARSCH,
                   NO_SCH_FILE, NO_PCB_FILE, W_VARPCB, NO_YAML_MODULE, WRONG_ARGUMENTS, FAILED_EXECUTE,
                   MOD_EXCLUDE_FROM_POS_FILES, MOD_EXCLUDE_FROM_BOM, MOD_BOARD_ONLY, hide_stderr)
from .error import PlotError, KiPlotConfigurationError, config_error, trace_dump
from .config_reader import CfgYamlReader
from .pre_base import BasePreFlight
from .dep_downloader import register_deps
import kibot.dep_downloader as dep_downloader
from .kicad.v5_sch import Schematic, SchFileError, SchError
from .kicad.v6_sch import SchematicV6
from .kicad.config import KiConfError
from . import log

logger = log.get_logger()
# Cache to avoid running external many times to check their versions
script_versions = {}
actions_loaded = False
needed_imports = set()

try:
    import yaml
except ImportError:
    log.init()
    logger.error('No yaml module for Python, install python3-yaml')
    logger.error(TRY_INSTALL_CHECK)
    exit(NO_YAML_MODULE)


def cased_path(path):
    r = glob(re.sub(r'([^:/\\])(?=[/\\]|$)|\[', r'[\g<0>]', path))
    return r and r[0] or path


def try_register_deps(mod, name):
    if mod.__doc__:
        try:
            data = yaml.safe_load(mod.__doc__)
        except yaml.YAMLError as e:
            logger.error('While loading plug-in `{}`:'.format(name))
            config_error("Error loading YAML "+str(e))
        register_deps(name, data)


def _import(name, path):
    # Python 3.4+ import mechanism
    spec = spec_from_file_location("kibot."+name, path)
    mod = module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except ImportError as e:
        trace_dump()
        logger.error('Unable to import plug-ins: '+str(e))
        logger.error('Make sure you used `--no-compile` if you used pip for installation')
        logger.error('Python path: '+str(sys_path))
        exit(WRONG_INSTALL)
    try_register_deps(mod, name)


def _load_actions(path, load_internals=False):
    logger.debug("Importing from "+path)
    lst = glob(os.path.join(path, 'out_*.py')) + glob(os.path.join(path, 'pre_*.py'))
    lst += glob(os.path.join(path, 'var_*.py')) + glob(os.path.join(path, 'fil_*.py'))
    if load_internals:
        lst += [os.path.join(path, 'globals.py')]
    for p in sorted(lst):
        name = os.path.splitext(os.path.basename(p))[0]
        logger.debug("- Importing "+name)
        _import(name, p)


def load_actions():
    """ Load all the available outputs and preflights """
    global actions_loaded
    if actions_loaded:
        return
    actions_loaded = True
    try_register_deps(dep_downloader, 'global')
    from kibot.mcpyrate import activate
    # activate.activate()
    _load_actions(os.path.abspath(os.path.dirname(__file__)), True)
    home = os.environ.get('HOME')
    if home:
        dir = os.path.join(home, '.config', 'kiplot', 'plugins')
        if os.path.isdir(dir):
            _load_actions(dir)
        dir = os.path.join(home, '.config', 'kibot', 'plugins')
        if os.path.isdir(dir):
            _load_actions(dir)
    # de_activate in old mcpy
    if 'deactivate' in activate.__dict__:
        logger.debug('Deactivating macros')
        activate.deactivate()


def extract_errors(text):
    in_error = in_warning = False
    msg = ''
    for line in text.split('\n'):
        line += '\n'
        if line[0] == ' ' and (in_error or in_warning):
            msg += line
        else:
            if in_error:
                in_error = False
                logger.error(msg.rstrip())
            elif in_warning:
                in_warning = False
                logger.warning(W_KIAUTO+msg.rstrip())
        if line.startswith('ERROR:'):
            in_error = True
            msg = line[6:]
        elif line.startswith('WARNING:'):
            in_warning = True
            msg = line[8:]
    if in_error:
        in_error = False
        logger.error(msg.rstrip())
    elif in_warning:
        in_warning = False
        logger.warning(W_KIAUTO+msg.rstrip())


def debug_output(res):
    if res.stdout:
        logger.debug('- Output from command: '+res.stdout.decode())


def _run_command(command, change_to):
    return run(command, check=True, stdout=PIPE, stderr=STDOUT, cwd=change_to)


def run_command(command, change_to=None, just_raise=False, use_x11=False):
    logger.debug('Executing: '+shlex.join(command))
    if change_to is not None:
        logger.debug('- CWD: '+change_to)
    try:
        if use_x11 and not GS.on_windows:
            logger.debug('Using Xvfb to run the command')
            from xvfbwrapper import Xvfb
            with Xvfb(width=640, height=480, colordepth=24):
                res = _run_command(command, change_to)
        else:
            res = _run_command(command, change_to)
    except CalledProcessError as e:
        if just_raise:
            raise
        logger.error('Running {} returned {}'.format(e.cmd, e.returncode))
        debug_output(e)
        exit(FAILED_EXECUTE)
    debug_output(res)
    return res.stdout.decode().rstrip()


def exec_with_retry(cmd, exit_with=None):
    cmd_str = shlex.join(cmd)
    logger.debug('Executing: '+cmd_str)
    if GS.debug_level > 2:
        logger.debug('Command line: '+str(cmd))
    retry = 2
    while retry:
        result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        ret = result.returncode
        retry -= 1
        if ret != 16 and (ret > 0 and ret < 128 and retry):
            # 16 is KiCad crash
            logger.debug('Failed with error {}, retrying ...'.format(ret))
        else:
            extract_errors(result.stderr)
            err = '> '+result.stderr.replace('\n', '\n> ')
            logger.debug('Output from command:\n'+err)
            if 'Timed out' in err:
                logger.warning(W_TIMEOUT+'Time out detected, on slow machines or complex projects try:')
                logger.warning(W_TIMEOUT+'`kiauto_time_out_scale` and/or `kiauto_wait_start` global options')
            if exit_with is not None and ret:
                logger.error(cmd[0]+' returned %d', ret)
                exit(exit_with)
            return ret


def load_board(pcb_file=None, forced=False):
    if GS.board is not None and not forced:
        # Already loaded
        return GS.board
    import pcbnew
    if not pcb_file:
        GS.check_pcb()
        pcb_file = GS.pcb_file
    try:
        with hide_stderr():
            board = pcbnew.LoadBoard(pcb_file)
        if BasePreFlight.get_option('check_zone_fills'):
            pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        if GS.global_units and GS.ki6:
            # In KiCad 6 "dimensions" has units.
            # The default value is DIM_UNITS_MODE_AUTOMATIC.
            # But this has a meaning only in the GUI where you have default units.
            # So now we have global.units and here we patch the board.
            UNIT_NAME_TO_INDEX = {'millimeters': pcbnew.DIM_UNITS_MODE_MILLIMETRES,
                                  'inches': pcbnew.DIM_UNITS_MODE_INCHES,
                                  'mils': pcbnew.DIM_UNITS_MODE_MILS}
            forced_units = UNIT_NAME_TO_INDEX[GS.global_units]
            for dr in board.GetDrawings():
                if dr.GetClass().startswith('PCB_DIM_') and dr.GetUnitsMode() == pcbnew.DIM_UNITS_MODE_AUTOMATIC:
                    dr.SetUnitsMode(forced_units)
                    dr.Update()
        GS.board = board
    except OSError as e:
        logger.error('Error loading PCB file. Corrupted?')
        logger.error(e)
        exit(CORRUPTED_PCB)
    assert board is not None
    logger.debug("Board loaded")
    return board


def load_any_sch(file, project):
    if file[-9:] == 'kicad_sch':
        sch = SchematicV6()
        load_libs = False
    else:
        sch = Schematic()
        load_libs = True
    try:
        sch.load(file, project)
        if load_libs:
            sch.load_libs(file)
        if GS.debug_level > 1:
            logger.debug('Schematic dependencies: '+str(sch.get_files()))
    except SchFileError as e:
        trace_dump()
        logger.error('At line {} of `{}`: {}'.format(e.line, e.file, e.msg))
        logger.error('Line content: `{}`'.format(e.code))
        exit(CORRUPTED_SCH)
    except SchError as e:
        trace_dump()
        logger.error('While loading `{}`'.format(file))
        logger.error(str(e))
        exit(CORRUPTED_SCH)
    except KiConfError as e:
        trace_dump()
        logger.error('At line {} of `{}`: {}'.format(e.line, e.file, e.msg))
        logger.error('Line content: `{}`'.format(e.code))
        exit(EXIT_BAD_CONFIG)
    return sch


def load_sch():
    if GS.sch:  # Already loaded
        return
    GS.check_sch()
    GS.sch = load_any_sch(GS.sch_file, GS.sch_basename)


def get_board_comps_data(comps):
    """ Add information from the PCB to the list of components from the schematic.
        Note that we do it every time the function is called to reset transformation filters like rot_footprint. """
    if not GS.pcb_file:
        return
    load_board()
    # Each reference could be more than one sub-units
    # So this hash is ref -> [List of units]
    comps_hash = {}
    for c in comps:
        cur_list = comps_hash.get(c.ref, [])
        cur_list.append(c)
        comps_hash[c.ref] = cur_list
    for m in GS.get_modules():
        ref = m.GetReference()
        attrs = m.GetAttributes()
        if ref not in comps_hash:
            if not (attrs & MOD_BOARD_ONLY):
                logger.warning(W_PCBNOSCH + '`{}` component in board, but not in schematic'.format(ref))
            continue
        for c in comps_hash[ref]:
            c.bottom = m.IsFlipped()
            c.footprint_rot = m.GetOrientationDegrees()
            center = GS.get_center(m)
            c.footprint_x = center.x
            c.footprint_y = center.y
            (c.footprint_w, c.footprint_h) = GS.get_fp_size(m)
            c.has_pcb_info = True
            if GS.ki5:
                # KiCad 5
                if attrs == UI_SMD:
                    c.smd = True
                elif attrs == UI_VIRTUAL:
                    c.virtual = True
                else:
                    c.tht = True
            else:
                # KiCad 6
                if attrs & MOD_SMD:
                    c.smd = True
                if attrs & MOD_THROUGH_HOLE:
                    c.tht = True
                if attrs & MOD_VIRTUAL == MOD_VIRTUAL:
                    c.virtual = True
                if attrs & MOD_EXCLUDE_FROM_POS_FILES:
                    c.in_pos = False
                # The PCB contains another flag for the BoM
                # I guess it should be in sync, but: why should somebody want to unsync it?
                if attrs & MOD_EXCLUDE_FROM_BOM:
                    c.in_bom_pcb = False
                if attrs & MOD_BOARD_ONLY:
                    c.in_pcb_only = True


def preflight_checks(skip_pre, targets):
    logger.debug("Preflight checks")

    if skip_pre is not None:
        if skip_pre == 'all':
            logger.debug("Skipping all preflight actions")
            return
        else:
            skip_list = skip_pre.split(',')
            for skip in skip_list:
                if skip == 'all':
                    logger.error('All can\'t be part of a list of actions '
                                 'to skip. Use `--skip all`')
                    exit(EXIT_BAD_ARGS)
                else:
                    if not BasePreFlight.is_registered(skip):
                        logger.error('Unknown preflight `{}`'.format(skip))
                        exit(EXIT_BAD_ARGS)
                    o_pre = BasePreFlight.get_preflight(skip)
                    if not o_pre:
                        logger.warning(W_NONEEDSKIP + '`{}` preflight is not in use, no need to skip'.format(skip))
                    else:
                        logger.debug('Skipping `{}`'.format(skip))
                        o_pre.disable()
    BasePreFlight.run_enabled(targets)


def get_output_dir(o_dir, obj, dry=False):
    # outdir is a combination of the config and output
    outdir = os.path.abspath(obj.expand_dirname(os.path.join(GS.out_dir, o_dir)))
    # Create directory if needed
    logger.debug("Output destination: {}".format(outdir))
    if not dry and not os.path.exists(outdir):
        os.makedirs(outdir)
    return outdir


def config_output(out, dry=False, dont_stop=False):
    if out._configured:
        return True
    # Should we load the PCB?
    if not dry:
        if out.is_pcb():
            load_board()
        if out.is_sch():
            load_sch()
    ok = True
    try:
        out.config(None)
    except KiPlotConfigurationError as e:
        msg = "In section '"+out.name+"' ("+out.type+"): "+str(e)
        if dont_stop:
            logger.error(msg)
        else:
            config_error(msg)
        ok = False
    except SystemExit:
        if not dont_stop:
            raise
        ok = False
    return ok


def get_output_targets(output, parent):
    out = RegOutput.get_output(output)
    if out is None:
        logger.error('Unknown output `{}` selected in {}'.format(output, parent))
        exit(WRONG_ARGUMENTS)
    config_output(out)
    out_dir = get_output_dir(out.dir, out, dry=True)
    files_list = out.get_targets(out_dir)
    return files_list, out_dir, out


def run_output(out, dont_stop=False):
    if out._done:
        return
    if GS.global_set_text_variables_before_output and hasattr(out.options, 'variant'):
        pre = BasePreFlight.get_preflight('set_text_variables')
        if pre:
            pre._variant = out.options.variant
            pre.apply()
            load_board()
    GS.current_output = out.name
    try:
        out.run(get_output_dir(out.dir, out))
        out._done = True
    except PlotError as e:
        logger.error("In output `"+str(out)+"`: "+str(e))
        if not dont_stop:
            exit(PLOT_ERROR)
    except KiPlotConfigurationError as e:
        msg = "In section '"+out.name+"' ("+out.type+"): "+str(e)
        if dont_stop:
            logger.error(msg)
        else:
            config_error(msg)
    except SystemExit:
        if not dont_stop:
            raise


def configure_and_run(tree, out_dir, msg):
    out = RegOutput.get_class_for(tree['type'])()
    out.set_tree(tree)
    config_output(out)
    logger.debug(' - Creating the PCB3D ...')
    out.run(out_dir)


def _generate_outputs(outputs, targets, invert, skip_pre, cli_order, no_priority, dont_stop):
    logger.debug("Starting outputs for board {}".format(GS.pcb_file))
    # Make a list of target outputs
    n = len(targets)
    if n == 0:
        # No targets means all
        if invert:
            # Skip all targets
            logger.debug('Skipping all outputs')
        else:
            targets = [out for out in RegOutput.get_outputs() if out.run_by_default]
    else:
        # Check we got a valid list of outputs
        unknown = next(filter(lambda x: not RegOutput.is_output_or_group(x), targets), None)
        if unknown:
            logger.error('Unknown output/group `{}`'.format(unknown))
            exit(EXIT_BAD_ARGS)
        # Check for CLI+invert inconsistency
        if cli_order and invert:
            logger.error("CLI order and invert options can't be used simultaneously")
            exit(EXIT_BAD_ARGS)
        # Expand groups
        logger.debug('Outputs before groups expansion: {}'.format(targets))
        try:
            targets = RegOutput.solve_groups(targets, 'command line')
        except KiPlotConfigurationError as e:
            config_error(str(e))
        logger.debug('Outputs after groups expansion: {}'.format(targets))
        # Now convert the list of names into a list of output objects
        if cli_order:
            # Add them in the same order found at the command line
            targets = [RegOutput.get_output(name) for name in targets]
        else:
            # Add them in the declared order
            new_targets = []
            if invert:
                # Invert the selection
                for out in RegOutput.get_outputs():
                    if (out.name not in targets) and out.run_by_default:
                        new_targets.append(out)
                    else:
                        logger.debug('Skipping `{}` output'.format(out.name))
            else:
                # Normal list
                for out in RegOutput.get_outputs():
                    if out.name in targets:
                        new_targets.append(out)
                    else:
                        logger.debug('Skipping `{}` output'.format(out.name))
            targets = new_targets
    logger.debug('Outputs before preflights: {}'.format([t.name for t in targets]))
    # Run the preflights
    preflight_checks(skip_pre, targets)
    logger.debug('Outputs after preflights: {}'.format([t.name for t in targets]))
    if not cli_order and not no_priority:
        # Sort by priority
        targets = sorted(targets, key=lambda o: o.priority, reverse=True)
        logger.debug('Outputs after sorting: {}'.format([t.name for t in targets]))
    # Configure and run the outputs
    for out in targets:
        if config_output(out, dont_stop=dont_stop):
            logger.info('- '+str(out))
            run_output(out, dont_stop)


def generate_outputs(outputs, targets, invert, skip_pre, cli_order, no_priority, dont_stop=False):
    prj = None
    if GS.global_restore_project:
        # Memorize the project content to restore it at exit
        prj = GS.read_pro()
    try:
        _generate_outputs(outputs, targets, invert, skip_pre, cli_order, no_priority, dont_stop)
    finally:
        # Restore the project file
        GS.write_pro(prj)


def adapt_file_name(name):
    if not name.startswith('/usr'):
        name = os.path.relpath(name)
    name = name.replace(' ', r'\ ')
    if '$' in name:
        logger.warning(W_WRONGCHAR+'Wrong character in file name `{}`'.format(name))
    return name


def gen_global_targets(f, pre_targets, out_targets, type):
    extra_targets = []
    pre = 'pre_'+type
    out = 'out_'+type
    all = 'all_'+type
    if pre_targets:
        f.write('{}:{}\n\n'.format(pre, pre_targets))
        extra_targets.append(pre)
    if out_targets:
        f.write('{}:{}\n\n'.format(out, out_targets))
        extra_targets.append(out)
    if pre_targets or out_targets:
        tg = ''
        if pre_targets:
            tg = ' '+pre
        if out_targets:
            tg += ' '+out
        f.write('{}:{}\n\n'.format(all, tg))
        extra_targets.append(all)
    return extra_targets


def get_pre_targets(targets, dependencies, is_pre):
    pcb_targets = sch_targets = ''
    prefs = BasePreFlight.get_in_use_objs()
    try:
        for pre in prefs:
            tg = pre.get_targets()
            if not tg:
                continue
            name = pre._name
            targets[name] = [adapt_file_name(fn) for fn in tg]
            dependencies[name] = [adapt_file_name(fn) for fn in pre.get_dependencies()]
            is_pre.add(name)
            if pre.is_sch():
                sch_targets += ' '+name
            if pre.is_pcb():
                pcb_targets += ' '+name
    except KiPlotConfigurationError as e:
        config_error("In preflight '"+name+"': "+str(e))
    return pcb_targets, sch_targets


def get_out_targets(outputs, ori_names, targets, dependencies, comments, no_default):
    pcb_targets = sch_targets = ''
    try:
        for out in outputs:
            name = name2make(out.name)
            ori_names[name] = out.name
            tg = out.get_targets(out.expand_dirname(os.path.join(GS.out_dir, out.dir)))
            if not tg:
                continue
            targets[name] = [adapt_file_name(fn) for fn in tg]
            dependencies[name] = [adapt_file_name(fn) for fn in out.get_dependencies()]
            if out.comment:
                comments[name] = out.comment
            if not out.run_by_default:
                no_default.add(name)
            if out.is_sch():
                sch_targets += ' '+name
            if out.is_pcb():
                pcb_targets += ' '+name
    except KiPlotConfigurationError as e:
        config_error("In output '"+name+"': "+str(e))
    return pcb_targets, sch_targets


def generate_makefile(makefile, cfg_file, outputs, kibot_sys=False):
    cfg_file = os.path.relpath(cfg_file)
    logger.info('- Creating makefile `{}` from `{}`'.format(makefile, cfg_file))
    with open(makefile, 'wt') as f:
        f.write('#!/usr/bin/make\n')
        f.write('# Automatically generated by KiBot from `{}`\n'.format(cfg_file))
        fname = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'kibot'))
        if kibot_sys or not os.path.isfile(fname):
            fname = 'kibot'
        f.write('KIBOT?={}\n'.format(fname))
        dbg = ''
        if GS.debug_level > 0:
            dbg = '-'+'v'*GS.debug_level
        f.write('DEBUG?={}\n'.format(dbg))
        f.write('CONFIG={}\n'.format(cfg_file))
        if GS.sch_file:
            f.write('SCH={}\n'.format(os.path.relpath(GS.sch_file)))
        if GS.pcb_file:
            f.write('PCB={}\n'.format(os.path.relpath(GS.pcb_file)))
        f.write('DEST={}\n'.format(os.path.relpath(GS.out_dir)))
        f.write('KIBOT_CMD=$(KIBOT) $(DEBUG) -c $(CONFIG) -e $(SCH) -b $(PCB) -d $(DEST)\n')
        f.write('LOGFILE?=kibot_error.log\n')
        f.write('\n')
        # Configure all outputs
        for out in outputs:
            config_output(out)
        # Get all targets and dependencies
        targets = OrderedDict()
        dependencies = OrderedDict()
        comments = {}
        ori_names = {}
        is_pre = set()
        no_default = set()
        # Preflights
        pre_pcb_targets, pre_sch_targets = get_pre_targets(targets, dependencies, is_pre)
        # Outputs
        out_pcb_targets, out_sch_targets = get_out_targets(outputs, ori_names, targets, dependencies, comments, no_default)
        # all target
        f.write('#\n# Default target\n#\n')
        f.write('all: '+' '.join(filter(lambda x: x not in no_default, targets.keys()))+'\n\n')
        extra_targets = ['all']
        # PCB/SCH specific targets
        f.write('#\n# SCH/PCB targets\n#\n')
        extra_targets.extend(gen_global_targets(f, pre_sch_targets, out_sch_targets, 'sch'))
        extra_targets.extend(gen_global_targets(f, pre_pcb_targets, out_pcb_targets, 'pcb'))
        # Generate the output targets
        f.write('#\n# Available targets (outputs)\n#\n')
        for name, target in targets.items():
            f.write(name+': '+' '.join(target)+'\n\n')
        # Generate the output dependencies
        f.write('#\n# Rules and dependencies\n#\n')
        if GS.debug_enabled:
            kibot_cmd = '\t$(KIBOT_CMD)'
            log_action = ''
        else:
            kibot_cmd = '\t@$(KIBOT_CMD)'
            log_action = ' 2>> $(LOGFILE)'
        for name, dep in dependencies.items():
            if name in comments:
                f.write('# '+comments[name]+'\n')
            dep.append(cfg_file)
            f.write(' '.join(targets[name])+': '+' '.join(dep)+'\n')
            if name in is_pre:
                skip = filter(lambda n: n != name, is_pre)
                f.write('{} -s {} -i{}\n\n'.format(kibot_cmd, ','.join(skip), log_action))
            else:
                f.write('{} -s all "{}"{}\n\n'.format(kibot_cmd, ori_names[name], log_action))
        # Mark all outputs as PHONY
        f.write('.PHONY: '+' '.join(extra_targets+list(targets.keys()))+'\n')


def guess_ki6_sch(schematics):
    schematics = list(filter(lambda x: x.endswith('.kicad_sch'), schematics))
    if len(schematics) == 1:
        return schematics[0]
    if len(schematics) == 0:
        return None
    for fname in schematics:
        with open(fname, 'rt') as f:
            text = f.read()
        if 'sheet_instances' in text:
            return fname
    return None


def solve_schematic(base_dir, a_schematic=None, a_board_file=None, config=None, sug_e=True):
    schematic = a_schematic
    if not schematic and a_board_file:
        base = os.path.splitext(a_board_file)[0]
        sch = os.path.join(base_dir, base+'.sch')
        if os.path.isfile(sch):
            schematic = sch
        else:
            sch = os.path.join(base_dir, base+'.kicad_sch')
            if os.path.isfile(sch):
                schematic = sch
    if not schematic:
        schematics = glob(os.path.join(base_dir, '*.sch'))
        if GS.ki6:
            schematics += glob(os.path.join(base_dir, '*.kicad_sch'))
        if len(schematics) == 1:
            schematic = schematics[0]
            logger.info('Using SCH file: '+os.path.relpath(schematic))
        elif len(schematics) > 1:
            # Look for a schematic with the same name as the config
            if config:
                if config[0] == '.':
                    # Unhide hidden config
                    config = config[1:]
                # Remove any extension
                while '.' in config:
                    config = os.path.splitext(config)[0]
                # Try KiCad 5
                sch = os.path.join(base_dir, config+'.sch')
                if os.path.isfile(sch):
                    schematic = sch
                elif GS.ki6:
                    # Try KiCad 6
                    sch = os.path.join(base_dir, config+'.kicad_sch')
                    if os.path.isfile(sch):
                        schematic = sch
            if not schematic:
                # Look for a schematic with a PCB and/or project
                for sch in schematics:
                    base = os.path.splitext(sch)[0]
                    if (os.path.isfile(os.path.join(base_dir, base+'.pro')) or
                       os.path.isfile(os.path.join(base_dir, base+'.kicad_pro')) or
                       os.path.isfile(os.path.join(base_dir, base+'.kicad_pcb'))):
                        schematic = sch
                        break
                else:
                    # No way to select one, just take the first
                    if GS.ki6:
                        schematic = guess_ki6_sch(schematics)
                    if not schematic:
                        schematic = schematics[0]
            msg = ' if you want to use another use -e option' if sug_e else ''
            logger.warning(W_VARSCH + 'More than one SCH file found in `'+base_dir+'`.\n'
                           '  Using '+schematic+msg+'.')
    if schematic and not os.path.isfile(schematic):
        logger.error("Schematic file not found: "+schematic)
        exit(NO_SCH_FILE)
    if schematic:
        schematic = os.path.abspath(schematic)
        logger.debug('Using schematic: `{}`'.format(schematic))
        logger.debug('Real schematic name: `{}`'.format(cased_path(schematic)))
    else:
        logger.debug('No schematic file found')
    return schematic


def check_board_file(board_file):
    if board_file and not os.path.isfile(board_file):
        logger.error("Board file not found: "+board_file)
        exit(NO_PCB_FILE)


def solve_board_file(base_dir, a_board_file=None, sug_b=True):
    schematic = GS.sch_file
    board_file = a_board_file
    if not board_file and schematic:
        pcb = os.path.join(base_dir, os.path.splitext(schematic)[0]+'.kicad_pcb')
        if os.path.isfile(pcb):
            board_file = pcb
    if not board_file:
        board_files = glob(os.path.join(base_dir, '*.kicad_pcb'))
        if len(board_files) == 1:
            board_file = board_files[0]
            logger.info('Using PCB file: '+os.path.relpath(board_file))
        elif len(board_files) > 1:
            board_file = board_files[0]
            msg = ' if you want to use another use -b option' if sug_b else ''
            logger.warning(W_VARPCB + 'More than one PCB file found in `'+base_dir+'`.\n'
                           '  Using '+board_file+msg+'.')
    check_board_file(board_file)
    if board_file:
        logger.debug('Using PCB: `{}`'.format(board_file))
        logger.debug('Real PCB name: `{}`'.format(cased_path(board_file)))
    else:
        logger.debug('No PCB file found')
    return board_file


def solve_project_file():
    if GS.pcb_file:
        pro_name = GS.pcb_no_ext+GS.pro_ext
        if os.path.isfile(pro_name):
            return pro_name
    if GS.sch_file:
        pro_name = GS.sch_no_ext+GS.pro_ext
        if os.path.isfile(pro_name):
            return pro_name
    return None


def look_for_used_layers():
    from .layer import Layer
    Layer.reset()
    layers = set()
    components = {}
    # Look inside the modules
    for m in GS.get_modules():
        layer = m.GetLayer()
        components[layer] = components.get(layer, 0)+1
        for gi in m.GraphicalItems():
            layers.add(gi.GetLayer())
        for pad in m.Pads():
            for id in pad.GetLayerSet().Seq():
                layers.add(id)
    # All drawings in the PCB
    for e in GS.board.GetDrawings():
        layers.add(e.GetLayer())
    # Zones
    for e in list(GS.board.Zones()):
        layers.add(e.GetLayer())
    # Tracks and vias
    via_type = 'VIA' if GS.ki5 else 'PCB_VIA'
    for e in GS.board.GetTracks():
        if e.GetClass() == via_type:
            for id in e.GetLayerSet().Seq():
                layers.add(id)
        else:
            layers.add(e.GetLayer())
    # Now filter the pads and vias potential layers
    declared_layers = {la._id for la in Layer.solve('all')}
    layers = sorted(declared_layers.intersection(layers))
    logger.debug('- Detected layers: {}'.format(layers))
    layers = Layer.solve(layers)
    for la in layers:
        la.components = components.get(la._id, 0)
    return layers


def discover_files(dest_dir):
    """ Look for schematic and PCBs at the dest_dir.
        Return the name of the example file to generate. """
    GS.pcb_file = None
    GS.sch_file = None
    # Check if we have useful files
    fname = os.path.join(dest_dir, 'kibot_generated.kibot.yaml')
    GS.set_sch(solve_schematic(dest_dir, sug_e=False))
    GS.set_pcb(solve_board_file(dest_dir, sug_b=False))
    GS.set_pro(solve_project_file())
    return fname


def yaml_dump(f, tree):
    if version_str2tuple(yaml.__version__) < (3, 14):
        f.write(yaml.dump(tree))
    else:
        # sort_keys was introduced after 3.13
        f.write(yaml.dump(tree, sort_keys=False))


def register_xmp_import(name):
    """ Register an import we need for an example """
    global needed_imports
    needed_imports.add(name)


def generate_one_example(dest_dir, types):
    """ Generate a example config for dest_dir """
    fname = discover_files(dest_dir)
    # Abort if none
    if not GS.pcb_file and not GS.sch_file:
        return None
    # Reset the board and schematic
    GS.board = None
    GS.sch = None
    # Create the config
    with open(fname, 'wt') as f:
        logger.info('- Creating {} example configuration'.format(fname))
        f.write("# This is a working example.\n")
        f.write("# For a more complete reference use `--example`\n")
        f.write('kibot:\n  version: 1\n\n')
        # Outputs
        outs = RegOutput.get_registered()
        # List of layers
        layers = []
        if GS.pcb_file:
            load_board(GS.pcb_file)
            layers = look_for_used_layers()
        if GS.sch_file:
            load_sch()
        # Filter some warnings
        fil = [{'number': 1007},  # No information for a component in a distributor
               {'number': 1015},  # More than one component in a search for a distributor
               {'number': 58},    # Missing project file
               ]
        glb = {'filters': fil}
        yaml_dump(f, {'global': glb})
        f.write('\n')
        # A helper for the internal templates
        global needed_imports
        needed_imports = set()
        # All the outputs
        outputs = []
        for n, cls in OrderedDict(sorted(outs.items())).items():
            o = cls()
            if types and n not in types:
                logger.debug('- {}, not selected (PCB: {} SCH: {})'.format(n, o.is_pcb(), o.is_sch()))
                continue
            if ((not(o.is_pcb() and GS.pcb_file) and not(o.is_sch() and GS.sch_file)) or
               ((o.is_pcb() and o.is_sch()) and (not GS.pcb_file or not GS.sch_file))):
                logger.debug('- {}, skipped (PCB: {} SCH: {})'.format(n, o.is_pcb(), o.is_sch()))
                continue
            # Look for templates
            tpls = glob(os.path.join(GS.get_resource_path('config_templates'), n, '*.kibot.yaml'))
            if tpls:
                # Load the templates
                tpl_names = tpls
                tpls = []
                for t in tpl_names:
                    tree = yaml.safe_load(open(t))
                    tpls.append(tree['outputs'])
                    imps = tree.get('import')
                    if imps:
                        needed_imports.update([imp['file'] for imp in imps])
            tree = cls.get_conf_examples(n, layers, tpls)
            if tree:
                logger.debug('- {}, generated'.format(n))
                if tpls:
                    logger.debug(' - Templates: {}'.format(tpl_names))
                outputs.extend(tree)
            else:
                logger.debug('- {}, nothing to do'.format(n))
        if needed_imports:
            imports = [{'file': man} for man in sorted(needed_imports)]
            yaml_dump(f, {'import': imports})
            f.write('\n')
        if outputs:
            yaml_dump(f, {'outputs': outputs})
        else:
            return None
    return fname


def generate_targets(config_file):
    """ Generate all possible targets for the configuration file """
    # Reset the board and schematic
    GS.board = None
    GS.sch = None
    # Reset the list of outputs
    RegOutput.reset()
    # Read the config file
    cr = CfgYamlReader()
    with open(config_file) as cf_file:
        outputs = cr.read(cf_file)
    # Do all the job
    generate_outputs(outputs, [], False, None, False, False, dont_stop=True)


def _walk(path, depth):
    """ Recursively list files and directories up to a certain depth """
    depth -= 1
    with os.scandir(path) as p:
        for entry in p:
            yield entry.path
            if entry.is_dir() and depth > 0:
                yield from _walk(entry.path, depth)


def generate_examples(start_dir, dry, types):
    if not start_dir:
        start_dir = '.'
    else:
        if not os.path.isdir(start_dir):
            logger.error('Invalid dir {} to quick start'.format(start_dir))
            exit(WRONG_ARGUMENTS)
    # Set default global options
    glb = GS.class_for_global_opts()
    glb.set_tree({})
    glb.config(None)
    # Look for candidate dirs
    k_files_regex = re.compile(r'([^/]+)\.(kicad_pcb|kicad_sch|sch)$')
    candidates = set()
    for f in _walk(start_dir, 6):
        if k_files_regex.search(f):
            candidates.add(os.path.dirname(f))
    # Try to generate the configs in the candidate places
    confs = []
    for c in sorted(candidates):
        logger.info('Analyzing `{}` dir'.format(c))
        res = generate_one_example(c, types)
        if res:
            confs.append(res)
        logger.info('')
    confs.sort()
    # Just the configs, not the targets
    if dry:
        return
    # Try to generate all the stuff
    if GS.out_dir_in_cmd_line:
        out_dir = GS.out_dir
    else:
        out_dir = 'Generated'
    for n, c in enumerate(confs):
        conf_dir = os.path.dirname(c)
        if len(confs) > 1:
            subdir = '%03d-%s' % (n+1, conf_dir.replace('/', ',').replace(' ', '_'))
            dest = os.path.join(out_dir, subdir)
        else:
            dest = out_dir
        GS.out_dir = dest
        logger.info('Generating targets for `{}`, destination: `{}`'.format(c, dest))
        os.makedirs(dest, exist_ok=True)
        # Create a log file with all the debug we can
        fl = log.set_file_log(os.path.join(dest, 'kibot.log'))
        old_lvl = GS.debug_level
        GS.debug_level = 10
        # Detect the SCH and PCB again
        discover_files(conf_dir)
        # Generate all targets
        generate_targets(c)
        # Close the debug file
        log.remove_file_log(fl)
        GS.debug_level = old_lvl
        logger.info('')
    # Try to open a browser
    index = os.path.join(GS.out_dir, 'index.html')
    if os.environ.get('DISPLAY') and which('x-www-browser') and os.path.isfile(index):
        Popen(['x-www-browser', index])


# To avoid circular dependencies: Optionable needs it, but almost everything needs Optionable
GS.load_board = load_board
GS.load_sch = load_sch
GS.exec_with_retry = exec_with_retry
