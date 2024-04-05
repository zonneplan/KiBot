# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# https://gitlab.com/kicad/code/kicad/-/blob/master/resources/schemas/drc.v1.json?ref_type=heads
import csv
import io
import json
import os
from . import __version__
from .bom.kibot_logo import KIBOT_LOGO, KIBOT_LOGO_W, KIBOT_LOGO_H
from .pre_filters import FilterOptions, FiltersOptions
from .macros import macros, document, pre_class  # noqa: F401
from .gs import GS
from .optionable import Optionable
from .kiplot import load_board, run_command
from .error import KiPlotConfigurationError
from .misc import (DRC_ERROR, STYLE_COMMON, TABLE_MODERN, HEAD_COLOR_B, HEAD_COLOR_B_L, TD_ERC_CLASSES, GENERATOR_CSS,
                   W_DRC, W_FILXRC, W_DRCJSON)
from .log import get_logger
logger = get_logger(__name__)
JSON_SECTIONS = ('violations', 'unconnected_items', 'schematic_parity')
SECTION_HUMAN = {'schematic_parity': 'Schematic parity', 'unconnected_items': 'Unconnected items', 'violations': 'Violations'}
SECTION_RPT = {'schematic_parity': 'Footprint errors', 'unconnected_items': 'unconnected pads', 'violations': 'DRC violations'}


def warning(msg):
    logger.warning(W_DRC+msg)


class FilterOptionsXRC(FilterOptions):
    def __init__(self):
        super().__init__()
        with document:
            self.change_to = 'ignore'
            """ [error,warning,ignore] The action of the filter.
                Changing to *ignore* is the default and is used to suppress a violation, but you can also change
                it to be an *error* or a *warning*. Note that violations excluded by KiCad are also analyzed,
                so you can revert a GUI exclusion """
        # number is for KiCad 5, remove it
        del self.number
        del self.error_number
        # Avoid mentioning KiCad 5/6 in the "error" help
        self.set_doc('error', " [string=''] Error id we want to exclude")


class DRCOptions(FiltersOptions):
    """ DRC options """
    def __init__(self):
        with document:
            self.enabled = True
            """ Enable the DRC. This is the replacement for the boolean value """
            self.dir = ''
            """ Sub-directory for the report """
            self.output = GS.def_global_output
            """ *Name for the generated archive (%i=erc %x=according to format) """
            self.format = Optionable
            """ [string|list(string)='HTML'][RPT,HTML,CSV,JSON] Format/s used for the report.
                You can specify multiple formats """
            self.warnings_as_errors = False
            """ DRC warnings are considered errors, they still reported as errors, but consider it an error """
            self.dont_stop = False
            """ Continue even if we detect DRC errors """
            self.units = 'millimeters'
            """ [millimeters,inches,mils] Units used for the positions. Affected by global options """
            self.schematic_parity = True
            """ Check if the PCB and the schematic are coincident """
            self.all_track_errors = False
            """ Report all the errors for all the tracks, not just the first """
            self.ignore_unconnected = False
            """ Ignores the unconnected nets. Useful if you didn't finish the routing """
        super().__init__()
        self.filters = FilterOptionsXRC
        self.set_doc('filters', " [list(dict)] Used to manipulate the DRC violations. Avoid using the *filters* preflight")
        self._unknown_is_error = True
        self._format_example = 'HTML,RPT'

    def config(self, parent):
        super().config(parent)
        self.format = Optionable.force_list(self.format)
        if not self.format:
            self.format = ['HTML']
        for f in self.format:
            if f not in {'RPT', 'HTML', 'CSV', 'JSON'}:
                raise KiPlotConfigurationError(f'unkwnown format `{f}`')


@pre_class
class DRC(BasePreFlight):  # noqa: F821
    """ [boolean=false|dict] Runs the DRC (Distance Rules Check). To ensure we have a valid PCB.
        This is a replacement for the *run_drc* preflight that needs KiCad 8 or newer.
        GUI exclusions and schematic parity are supported """
    def __init__(self, name, value):
        super().__init__(name, value)
        if isinstance(value, bool):
            f = DRCOptions()
            f.enabled = value
            f.format = ['HTML']
        elif isinstance(value, dict):
            f = DRCOptions()
            f.set_tree(value)
            f.config(self)
        else:
            raise KiPlotConfigurationError('must be boolean or dict')
        # Transfer the options to this class
        for k, v in dict(f.get_attrs_gen()).items():
            setattr(self, '_'+k, v)
        self._format = f.format
        self._filters = None if isinstance(f.filters, type) else f.unparsed
        self._pcb_related = True
        self._expand_id = 'drc'
        self._expand_ext = self._format[0].lower()

    def get_targets(self):
        """ Returns a list of targets generated by this preflight """
        load_board()
        out_dir = self.expand_dirname(GS.out_dir)
        if GS.global_dir and GS.global_use_dir_for_preflights:
            out_dir = os.path.join(out_dir, self.expand_dirname(GS.global_dir))
        names = []
        for f in self._format:
            self._expand_ext = f.lower()
            name = Optionable.expand_filename_pcb(self, self._output)
            names.append(os.path.abspath(os.path.join(out_dir, self._dir, name)))
        return names

    @classmethod
    def get_doc(cls):
        return cls.__doc__, DRCOptions

    def get_item_txt(self, item, indent=4, sep='\n'):
        desc = item.get('description', '')
        pos = item.get('pos', None)
        if pos:
            x = pos.get('x', 0)
            y = pos.get('y', 0)
            pos_txt = f'@({x} {self.units}, {y} {self.units}): '
        else:
            pos_txt = ''
        return (' '*indent)+f'{pos_txt}{desc}'+sep

    def apply_filters(self, data):
        filters = []
        if self._filters:
            filters += self._filters
        if GS.filters:
            logger.error(GS.filters)
            filters += GS.filters
            logger.warning(W_FILXRC+'Using filters from the `filters` preflight, move them to `drc`')
        self.c_err = self.c_warn = self.c_tot = 0
        self.c_err_excl = self.c_warn_excl = self.c_tot_excl = 0
        ign_unc = self._ignore_unconnected or BasePreFlight.get_option('ignore_unconnected')  # noqa: F821
        for section in JSON_SECTIONS:
            ignore = ign_unc and section == 'unconnected_items'
            for violation in data.get(section, []):
                severity = violation.get('severity', 'error')
                type = violation.get('type', '')
                # Collect the text using a layout equivalent to the report
                txt = violation.get('description', '')+'\n'
                for item in violation.get('items', []):
                    txt += self.get_item_txt(item)
                # Check if we want to exclude it
                excluded = violation.get('excluded')
                if ignore:
                    # Ignore unconnected enabled
                    if not excluded:
                        violation['excluded'] = True
                        violation['excluded_by_kibot'] = True
                        excluded = True
                else:
                    # Check if any filter matches this violation
                    for f in filters:
                        if type == f.error and f.regex.search(txt):
                            change_to = f.change_to if hasattr(f, 'change_to') else 'ignore'
                            if change_to == 'ignore':
                                if not excluded:
                                    violation['excluded'] = True
                                    violation['excluded_by_kibot'] = True
                                    excluded = True
                            else:
                                violation['excluded'] = False
                                violation['modified_by_kibot'] = True
                                severity = violation['severity'] = change_to
                                excluded = False
                            break
                if excluded:
                    if severity == 'error':
                        self.c_err_excl += 1
                    else:
                        self.c_warn_excl += 1
                    self.c_tot_excl += 1
                else:
                    if severity == 'error':
                        self.c_err += 1
                    else:
                        self.c_warn += 1
                    self.c_tot += 1

    def create_csv(self, data):
        f = io.StringIO()
        writer = csv.writer(f, delimiter=',', lineterminator="\n", quoting=csv.QUOTE_ALL)
        writer.writerow(['Check', 'Severity', 'Excluded', 'Type', 'Description', 'Details'])
        for section in JSON_SECTIONS:
            violations = data.get(section, [])
            name = SECTION_HUMAN[section]
            for violation in violations:
                severity = violation.get('severity', 'error')
                excluded = violation.get('excluded', False)
                type = violation.get('type', '')
                description = violation.get('description', '')
                details = ''
                for item in violation.get('items', []):
                    details += self.get_item_txt(item, indent=0, sep=';')
                writer.writerow([name, severity, excluded, type, description, details[:-1]])
        return f.getvalue()

    def add_html_violation(self, violation, html, i):
        severity = violation.get('severity', 'error')
        excluded = violation.get('excluded', False)
        type = violation.get('type', '')
        description = violation.get('description', '')
        details = ''
        for item in violation.get('items', []):
            details += self.get_item_txt(item, indent=0, sep='<br>')
        html += f'  <tr id="{i}">\n'
        cl = 'td-excluded' if excluded else ('td-error' if severity == 'error' else 'td-warning')
        html += f'   <td class="{cl}">{type}</td>\n'
        html += f'   <td>{description}</td>\n'
        html += f'   <td>{details}</td>\n'
        html += '  </tr>\n'
        return html

    def create_html(self, data):
        # HTML Head
        html = '<html>\n'
        html += '<head>\n'
        html += ' <meta charset="UTF-8">\n'  # UTF-8 encoding for unicode support
        title = 'DRC report for '+(GS.pro_basename or GS.sch_basename or '')
        html += f' <title>{title}</title>\n'
        # CSS
        html += '<style>\n'
        style = STYLE_COMMON
        style += TABLE_MODERN.replace('@bg@', HEAD_COLOR_B)
        style += TABLE_MODERN.replace('@bgl@', HEAD_COLOR_B_L)
        style += TD_ERC_CLASSES
        style += GENERATOR_CSS
        style += ' .head-table { margin-left: auto; margin-right: auto; }\n'
        style += ' .content-table { margin-left: auto; margin-right: auto }\n'
        html += style
        html += '</style>\n'
        html += '</head>\n'
        html += '<body>\n'

        img = 'data:image/png;base64,'+KIBOT_LOGO
        img_w = KIBOT_LOGO_W
        img_h = KIBOT_LOGO_H
        html += '<table class="head-table">\n'
        html += '<tr>\n'
        html += ' <td rowspan="3">\n'
        html += f'  <img src="{img}" alt="Logo" width="{img_w}" height="{img_h}">\n'
        html += ' </td>\n'
        html += ' <td colspan="2" class="cell-title">\n'
        html += f'  <div class="title">{title}</div>\n'
        html += ' </td>\n'
        html += '</tr>\n'
        html += '<tr>\n'
        html += ' <td class="cell-info">\n'
        html += f'   <b>PCB</b>: {GS.pcb_basename}<br>\n'
        html += f'   <b>Revision</b>: {GS.pcb_rev}<br>\n'
        dt = data.get('date', '??')
        html += f'   <b>Date</b>: {dt}<br>\n'
        kv = data.get('kicad_version', GS.kicad_version)
        html += f'   <b>KiCad Version</b>: {kv}<br>\n'
        html += ' </td>\n'
        html += ' <td class="cell-stats">\n'
        txt_error = f'<b>Errors</b>: {self.c_err}'+(f' (+{self.c_err_excl} excluded)' if self.c_err_excl else '')
        txt_warn = f'<b>Warnings</b>: {self.c_warn}'+(f' (+{self.c_warn_excl} excluded)' if self.c_warn_excl else '')
        txt_total = f'<b>Total</b>: {self.c_tot}'+(f' (+{self.c_tot_excl} excluded)' if self.c_tot_excl else '')
        html += f'   {txt_error}<br>\n'
        html += f'   {txt_warn}<br>\n'
        html += f'   {txt_total}<br>\n'
        html += ' </td>\n'
        html += '</tr>\n'
        html += '</table>\n'

        i = 0
        # Generate the content
        for section in JSON_SECTIONS:
            violations = data.get(section, [])
            if not violations:
                continue
            name = SECTION_HUMAN[section]
            html += f'<p class="subtitle">{name}</p>\n'
            html += '<table class="content-table">\n'
            html += ' <thead>\n'
            html += '  <tr>\n'
            for h in ['Type', 'Description', 'Details']:
                html += f'   <th>{h}</th>\n'
            html += '  </tr>\n'
            html += ' </thead>\n'
            html += ' <tbody>\n'
            # Errors
            for violation in violations:
                if violation.get('severity', 'error') == 'error' and not violation.get('excluded', False):
                    html = self.add_html_violation(violation, html, i)
                    i += 1
            # Warnings
            for violation in violations:
                if violation.get('severity', 'error') == 'warning' and not violation.get('excluded', False):
                    html = self.add_html_violation(violation, html, i)
                    i += 1
            # Excluded
            for violation in violations:
                if violation.get('excluded', False):
                    html = self.add_html_violation(violation, html, i)
                    i += 1
            html += ' </tbody>\n'
            html += '</table>\n'
        html += ('<p class="generator">Generated by <a href="https://github.com/INTI-CMNB/KiBot/">KiBot</a> v{}</p>\n'.
                 format(__version__))
        html += '</body>\n'
        html += '</html>\n'
        return html

    def create_json(self, data):
        return json.dumps(data, indent=4)

    def create_txt(self, data):
        dt = data.get('date', '??')
        rpt = f'** Drc report for {os.path.basename(GS.pcb_file)} **\n'
        rpt += f"** Created on {dt} **\n\n"
        for s in JSON_SECTIONS:
            violations = data.get(s, [])
            rpt += f'** Found {len(violations)} {SECTION_RPT[s]} **\n'
            for v in violations:
                severity = v.get('severity', 'error')
                type = v.get('type', '')
                description = v.get('description', '')
                rpt += f'[{type}]: {description}\n'
                excluded = ' (excluded)' if v.get('excluded') else ''
                rpt += f'    ; {severity}{excluded}\n'
                for item in v.get('items', []):
                    rpt += self.get_item_txt(item)
            rpt += '\n'
        rpt += '** End of Report **\n'
        return rpt

    def report(self, kind, count, data):
        if not count:
            return
        logf = logger.error if kind == 'error' else warning
        logf(f'{count} DRC {kind}s detected')
        for s in JSON_SECTIONS:
            check_name = SECTION_HUMAN[s]
            for v in data.get(s, []):
                if v.get('excluded'):
                    continue
                severity = v.get('severity', 'error')
                if severity != kind:
                    continue
                type = v.get('type', '')
                description = v.get('description', '')
                txt = f'({type}) {description}\n'
                for item in v.get('items', []):
                    txt += self.get_item_txt(item)
                txt += f'    Check: {check_name}'
                logf(txt)

    def run(self):
        if not GS.ki8:
            raise KiPlotConfigurationError('The `drc` preflight needs KiCad 8 or newer, use `run_drc` instead')
        # Compute the output name and make sure the path exists
        outputs = self.get_targets()
        output = outputs[0]
        os.makedirs(os.path.dirname(output), exist_ok=True)
        # Run the DRC from the CLI
        cmd = ['kicad-cli', 'pcb', 'drc', '-o', output, '--format', 'json', '--severity-all']
        if self._schematic_parity:
            cmd.append('--schematic-parity')
        if self._all_track_errors:
            cmd.append('--all-track-errors')
        logger.info('- Running the DRC')
        cmd.append(GS.pcb_file)
        run_command(cmd)
        # Read the result
        with open(output, 'rt') as f:
            raw = f.read()
            try:
                data = json.loads(raw)
            except json.decoder.JSONDecodeError:
                raise KiPlotConfigurationError(f"Corrupted DRC report `{output}`:\n{raw}")
        if data.get('$schema', '') != 'https://schemas.kicad.org/drc.v1.json':
            logger.warning(W_DRCJSON+'Unknown JSON schema, DRC might fail')
        self.units = data.get('coordinate_units', 'mm')
        # Apply KiBot filters
        self.apply_filters(data)
        # Generate the desired output format
        for (f, output) in zip(self._format, outputs):
            if f == 'CSV':
                res = self.create_csv(data)
            elif f == 'HTML':
                res = self.create_html(data)
            elif f == 'JSON':
                res = self.create_json(data)
            else:
                res = self.create_txt(data)
            # Write it to the output file
            with open(output, 'wt') as f:
                f.write(res)
        # Report the result
        self.report('error', self.c_err, data)
        self.report('warning', self.c_warn, data)
        # Check the final status
        error_level = 0 if self._dont_stop else DRC_ERROR
        if self.c_err:
            GS.exit_with_error(f'DRC errors: {self.c_err}', error_level)
        elif self.c_warn and (self._warnings_as_errors or BasePreFlight.get_option('erc_warnings')):  # noqa: F821
            GS.exit_with_error(f'DRC warnings: {self.c_warn}, promoted as errors', error_level)
