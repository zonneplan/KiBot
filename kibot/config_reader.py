# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
"""
Class to read KiBot config files
"""

import collections
import io
import os
import json
from sys import (exit, maxsize)
from collections import OrderedDict

from .error import KiPlotConfigurationError
from .misc import (NO_YAML_MODULE, EXIT_BAD_ARGS, EXAMPLE_CFG, WONT_OVERWRITE, W_NOOUTPUTS, W_UNKOUT, W_NOFILTERS,
                   W_NOVARIANTS, W_NOGLOBALS, TRY_INSTALL_CHECK, W_NOPREFLIGHTS, W_NOGROUPS)
from .gs import GS
from .registrable import RegOutput, RegVariant, RegFilter, RegDependency
from .pre_base import BasePreFlight
from . import __pypi_deps__
# Logger
from . import log

logger = log.get_logger()
LOCAL_OPTIONAL = 1
GLOBAL_OPTIONAL = LOCAL_OPTIONAL*100
LOCAL_MANDATORY = GLOBAL_OPTIONAL*100
GLOBAL_MANDATORY = LOCAL_MANDATORY*100
GITHUB_RAW = 'https://raw.githubusercontent.com/INTI-CMNB/KiBot/master/docs/images/'
DEB_LOGO = '![Debian]('+GITHUB_RAW+'debian-openlogo-22x22.png)'
PYPI_LOGO = ('![PyPi dependency]('+GITHUB_RAW+'PyPI_logo_simplified-22x22.png)')
PY_LOGO = ('![Python module]('+GITHUB_RAW+'Python-logo-notext-22x22.png)')
TOOL_LOGO = '![Tool]('+GITHUB_RAW+'llave-inglesa-22x22.png)'
AUTO_DOWN = '![Auto-download]('+GITHUB_RAW+'auto_download-22x22.png)'
VALID_SECTIONS = {'kiplot', 'kibot', 'import', 'global', 'filters', 'variants', 'preflight', 'outputs', 'groups'}
VALID_KIBOT_SEC = {'version', 'imported_global_has_less_priority'}


try:
    import yaml
except ImportError:
    log.init()
    logger.error('No yaml module for Python, install python3-yaml')
    logger.error(TRY_INSTALL_CHECK)
    exit(NO_YAML_MODULE)


def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        elif isinstance(v, list) and k in d:
            d[k] = v+d[k]
        else:
            d[k] = v
    return d


class CollectedImports(object):
    def __init__(self):
        super().__init__()
        self.outputs = []
        self.filters = {}
        self.variants = {}
        self.globals = {}
        self.preflights = []
        self.groups = {}
        self.imported_global_has_less_priority = False


class CfgYamlReader(object):
    def __init__(self):
        super().__init__()
        self.imported_globals = {}
        self.no_run_by_default = []
        self.imported_global_has_less_priority = False

    def _check_version(self, v):
        if not isinstance(v, dict):
            raise KiPlotConfigurationError("Incorrect `kibot` section")
        if 'version' not in v:
            raise KiPlotConfigurationError("YAML config needs `kibot.version`.")
        version = v['version']
        # Only version 1 is known
        if version != 1:
            raise KiPlotConfigurationError("Unknown KiBot config version: "+str(version))
        return version

    def _check_globals_priority(self, v):
        ops = 'imported_global_has_less_priority'
        if ops in v:
            value = v[ops]
            if not isinstance(value, bool):
                raise KiPlotConfigurationError(ops+" must be boolean")
            self.imported_global_has_less_priority = value

    def _parse_output(self, o_tree):
        try:
            name = str(o_tree['name'])
            if not name:
                raise KeyError
        except KeyError:
            raise KiPlotConfigurationError("Output needs a name in: "+str(o_tree))

        try:
            otype = o_tree['type']
            if not otype:
                raise KeyError
        except KeyError:
            raise KiPlotConfigurationError("Output `"+name+"` needs a type")

        try:
            comment = o_tree['comment']
        except KeyError:
            comment = ''
        if comment is None:
            comment = ''

        name_type = "`"+name+"` ("+otype+")"

        # Is a valid type?
        if not RegOutput.is_registered(otype):
            raise KiPlotConfigurationError("Unknown output type: `{}`".format(otype))
        # Load it
        logger.debug("Pre-parsing output options for "+name_type)
        o_out = RegOutput.get_class_for(otype)()
        o_out.set_tree(o_tree)
        # Set the data we already know, so we can skip the configurations that aren't requested
        o_out.name = name
        o_out.type = otype
        o_out.comment = comment
        o_out.extends = o_tree.get('extends', '')
        # Pre-parse the run_by_default option
        o_out.run_by_default = o_tree.get('run_by_default', True)
        if not isinstance(o_out.run_by_default, bool):
            o_out.run_by_default = True
        o_out.disable_run_by_default = o_tree.get('disable_run_by_default', '')
        # Pre-parse the disable_run_by_default option
        if isinstance(o_out.disable_run_by_default, str):
            if o_out.disable_run_by_default:
                self.no_run_by_default.append(o_out.disable_run_by_default)
        elif isinstance(o_out.disable_run_by_default, bool):
            # True means to disable the one we extend
            if o_out.disable_run_by_default and o_out.extends:
                self.no_run_by_default.append(o_out.extends)
        else:
            o_out.disable_run_by_default = ''
        return o_out

    def _parse_outputs(self, v):
        outputs = []
        if isinstance(v, list):
            for o in v:
                outputs.append(self._parse_output(o))
        else:
            raise KiPlotConfigurationError("`outputs` must be a list")
        return outputs

    def _parse_group(self, tree, groups):
        try:
            name = str(tree['name'])
            if not name:
                raise KeyError
        except KeyError:
            raise KiPlotConfigurationError("Group needs a name in: "+str(tree))
        try:
            outs = tree['outputs']
            if not outs:
                raise KeyError
        except KeyError:
            raise KiPlotConfigurationError("Group `"+name+"` must contain outputs")
        if not isinstance(outs, list):
            raise KiPlotConfigurationError("'outputs' in group `"+name+"` must be a list (not {})".format(type(outs)))
        for v in outs:
            if not isinstance(v, str):
                raise KiPlotConfigurationError("In group `"+name+"`: all outputs must be strings (not {})".format(type(v)))
        if name in groups:
            raise KiPlotConfigurationError("Duplicated group `{}`".format(name))
        groups[name] = outs

    def _parse_groups(self, v):
        groups = {}
        if isinstance(v, list):
            for o in v:
                self._parse_group(o, groups)
        else:
            raise KiPlotConfigurationError("`groups` must be a list")
        return groups

    def _parse_variant_or_filter(self, o_tree, kind, reg_class, is_internal=False):
        kind_f = kind[0].upper()+kind[1:]
        try:
            name = str(o_tree['name'])
            if not name:
                raise KeyError
        except KeyError:
            raise KiPlotConfigurationError(kind_f+" needs a name in: "+str(o_tree))
        try:
            otype = o_tree['type']
            if not otype:
                raise KeyError
        except KeyError:
            raise KiPlotConfigurationError(kind_f+" `"+name+"` needs a type")
        # Is a valid type?
        if not reg_class.is_registered(otype):
            raise KiPlotConfigurationError("Unknown {} type: `{}`".format(kind, otype))
        # Load it
        name_type = "`"+name+"` ("+otype+")"
        logger.debug("Parsing "+kind+" "+name_type)
        o_var = reg_class.get_class_for(otype)()
        o_var._internal = is_internal
        o_var.set_tree(o_tree)
        o_var.name = name
        o_var._name_type = name_type
        # Don't configure it yet, wait until we finish loading (could be an import)
        return o_var

    def _parse_variants(self, v, is_internal=False):
        variants = {}
        if isinstance(v, list):
            for o in v:
                o_var = self._parse_variant_or_filter(o, 'variant', RegVariant, is_internal)
                variants[o_var.name] = o_var
        else:
            raise KiPlotConfigurationError("`variants` must be a list")
        return variants

    def _parse_filters(self, v, is_internal=False):
        filters = {}
        if isinstance(v, list):
            for o in v:
                o_fil = self._parse_variant_or_filter(o, 'filter', RegFilter, is_internal)
                self.configure_variant_or_filter(o_fil)
                filters[o_fil.name] = o_fil
        else:
            raise KiPlotConfigurationError("`filters` must be a list")
        return filters

    def _parse_preflights(self, pf):
        logger.debug("Parsing preflight options: {}".format(pf))
        if not isinstance(pf, dict):
            raise KiPlotConfigurationError("Incorrect `preflight` section")

        preflights = []
        for k, v in pf.items():
            if not BasePreFlight.is_registered(k):
                raise KiPlotConfigurationError("Unknown preflight: `{}`".format(k))
            try:
                logger.debug("Parsing preflight "+k)
                o_pre = BasePreFlight.get_class_for(k)(k, v)
            except KiPlotConfigurationError as e:
                raise KiPlotConfigurationError("In preflight '"+k+"': "+str(e))
            preflights.append(o_pre)
        return preflights

    def _parse_global(self, gb):
        """ Get global options """
        logger.debug("Parsing global options: {}".format(gb))
        if not isinstance(gb, dict):
            raise KiPlotConfigurationError("Incorrect `global` section (must be a dict)")
        if self.imported_globals:
            if self.imported_global_has_less_priority:
                update_dict(self.imported_globals, gb)
                gb = self.imported_globals
            else:
                update_dict(gb, self.imported_globals)
            logger.debug("Global options + imported: {}".format(gb))
        # Parse all keys inside it
        glb = GS.class_for_global_opts()
        glb.set_tree(gb)
        try:
            glb.config(None)
        except KiPlotConfigurationError as e:
            raise KiPlotConfigurationError("In `global` section: "+str(e))

    @staticmethod
    def _config_error_import(fname, error):
        if fname is None:
            fname = '*unnamed*'
        raise KiPlotConfigurationError('{} in {} import'.format(error, fname))

    @staticmethod
    def _parse_import_items(kind, fname, value):
        if isinstance(value, str):
            if value == 'all':
                return None
            elif value == 'none':
                return []
            return [value]
        if isinstance(value, list):
            values = []
            for v in value:
                if isinstance(v, str):
                    values.append(v)
                else:
                    CfgYamlReader._config_error_import(fname, '`{}` items must be strings ({})'.format(kind, str(v)))
            return values
        CfgYamlReader._config_error_import(fname, '`{}` must be a string or a list ({})'.format(kind, str(v)))

    def _parse_import_outputs(self, outs, explicit_outs, fn_rel, data, imported):
        sel_outs = []
        if outs is None or len(outs) > 0:
            i_outs = imported.outputs
            if 'outputs' in data:
                i_outs += self._parse_outputs(data['outputs'])
            if outs is not None:
                for o in i_outs:
                    if o.name in outs:
                        sel_outs.append(o)
                        outs.remove(o.name)
                for o in outs:
                    logger.warning(W_UNKOUT+"can't import `{}` output from `{}` (missing)".format(o, fn_rel))
            else:
                sel_outs = i_outs
            if len(sel_outs) == 0:
                if explicit_outs:
                    logger.warning(W_NOOUTPUTS+"No outputs found in `{}`".format(fn_rel))
            else:
                logger.debug('Outputs loaded from `{}`: {}'.format(fn_rel, list(map(lambda c: c.name, sel_outs))))
        if outs is None and explicit_outs and 'outputs' not in data:
            logger.warning(W_NOOUTPUTS+"No outputs found in `{}`".format(fn_rel))
        return sel_outs

    def _parse_import_preflights(self, pre, explicit_pres, fn_rel, data, imported):
        sel_pres = []
        if pre is None or len(pre) > 0:
            i_pres = imported.preflights
            if 'preflight' in data:
                i_pres += self._parse_preflights(data['preflight'])
            if pre is not None:
                for p in i_pres:
                    if p._name in pre:
                        sel_pres.append(p)
                        pre.remove(p._name)
                for p in pre:
                    logger.warning(W_UNKOUT+"can't import `{}` preflight from `{}` (missing)".format(p, fn_rel))
            else:
                sel_pres = i_pres
            if len(sel_pres) == 0:
                if explicit_pres:
                    logger.warning(W_NOPREFLIGHTS+"No preflights found in `{}`".format(fn_rel))
            else:
                logger.debug('Preflights loaded from `{}`: {}'.format(fn_rel, list(map(lambda c: c._name, sel_pres))))
        if pre is None and explicit_pres and 'preflight' not in data:
            logger.warning(W_NOPREFLIGHTS+"No preflights found in `{}`".format(fn_rel))
        return sel_pres

    def _parse_import_filters(self, filters, explicit_fils, fn_rel, data, imported, is_internal):
        sel_fils = {}
        if filters is None or len(filters) > 0:
            if 'filters' in data:
                imported.filters.update(self._parse_filters(data['filters'], is_internal))
            i_fils = imported.filters
            if filters is not None:
                for f in filters:
                    if f in i_fils:
                        sel_fils[f] = i_fils[f]
                    else:
                        logger.warning(W_UNKOUT+"can't import `{}` filter from `{}` (missing)".format(f, fn_rel))
            else:
                sel_fils = i_fils
            if len(sel_fils) == 0:
                if explicit_fils:
                    logger.warning(W_NOFILTERS+"No filters found in `{}`".format(fn_rel))
            else:
                logger.debug('Filters loaded from `{}`: {}'.format(fn_rel, sel_fils.keys()))
        if filters is None and explicit_fils and 'filters' not in data:
            logger.warning(W_NOFILTERS+"No filters found in `{}`".format(fn_rel))
        return sel_fils

    def _parse_import_groups(self, groups, explicit_grps, fn_rel, data, imported):
        sel_grps = {}
        if groups is None or len(groups) > 0:
            if 'groups' in data:
                imported.groups.update(self._parse_groups(data['groups']))
            i_grps = imported.groups
            if groups is not None:
                for f in groups:
                    if f in i_grps:
                        sel_grps[f] = i_grps[f]
                    else:
                        logger.warning(W_UNKOUT+"can't import `{}` group from `{}` (missing)".format(f, fn_rel))
            else:
                sel_grps = i_grps
            if len(sel_grps) == 0:
                if explicit_grps:
                    logger.warning(W_NOGROUPS+"No groups found in `{}`".format(fn_rel))
            else:
                logger.debug('groups loaded from `{}`: {}'.format(fn_rel, sel_grps.keys()))
        if groups is None and explicit_grps and 'groups' not in data:
            logger.warning(W_NOGROUPS+"No groups found in `{}`".format(fn_rel))
        return sel_grps

    def _parse_import_variants(self, vars, explicit_vars, fn_rel, data, imported, is_internal):
        sel_vars = {}
        if vars is None or len(vars) > 0:
            if 'variants' in data:
                imported.variants.update(self._parse_variants(data['variants'], is_internal))
            i_vars = imported.variants
            if vars is not None:
                for f in vars:
                    if f in i_vars:
                        sel_vars[f] = i_vars[f]
                    else:
                        logger.warning(W_UNKOUT+"can't import `{}` variant from `{}` (missing)".format(f, fn_rel))
            else:
                sel_vars = i_vars
            if len(sel_vars) == 0:
                if explicit_vars:
                    logger.warning(W_NOVARIANTS+"No variants found in `{}`".format(fn_rel))
            else:
                logger.debug('Variants loaded from `{}`: {}'.format(fn_rel, sel_vars.keys()))
        if vars is None and explicit_vars and 'variants' not in data:
            logger.warning(W_NOVARIANTS+"No variants found in `{}`".format(fn_rel))
        return sel_vars

    def _parse_import_globals(self, globals, explicit_globals, fn_rel, data, imported):
        sel_globals = {}
        if (globals is None or len(globals) > 0):
            i_globals = data.get('global', {})
            if not isinstance(i_globals, dict):
                raise KiPlotConfigurationError("Incorrect `global` section (must be a dict), while importing from {}".
                                               format(fn_rel))
            update_dict(imported.globals, i_globals)
            i_globals = imported.globals
            if globals is not None:
                for f in globals:
                    if f in i_globals:
                        sel_globals[f] = i_globals[f]
                    else:
                        logger.warning(W_UNKOUT+"can't import `{}` global from `{}` (missing)".format(f, fn_rel))
            else:
                sel_globals = i_globals
            if len(sel_globals) == 0:
                if explicit_globals:
                    logger.warning(W_NOGLOBALS+"No globals found in `{}`".format(fn_rel))
            else:
                logger.debug('Globals loaded from `{}`: {}'.format(fn_rel, sel_globals.keys()))
        if globals is None and explicit_globals and 'global' not in data:
            logger.warning(W_NOGLOBALS+"No globals found in `{}`".format(fn_rel))
        return sel_globals

    def configure_variant_or_filter(self, o_var):
        o_var.config(None)

    def configure_variants(self, variants):
        logger.debug('Configuring variants')
        for o_var in variants.values():
            self.configure_variant_or_filter(o_var)

    def check_import_file_name(self, dir_name, fn, is_external):
        fn = os.path.expandvars(os.path.expanduser(fn))
        is_internal = False
        if not is_external and not os.path.splitext(fn)[1] and not os.path.isabs(fn):
            name = fn
            fn = os.path.join(GS.get_resource_path('config_templates'), fn+'.kibot.yaml')
            if not os.path.isfile(fn):
                fn_abs = os.path.join(dir_name, name)
                if not os.path.isfile(fn_abs):
                    raise KiPlotConfigurationError("Unknown internal import file `{}` ({})".format(name, fn))
                # Bizarre case: looks like an internal
                fn = fn_abs
            else:
                is_internal = True
        else:
            if not os.path.isabs(fn):
                fn = os.path.join(dir_name, fn)
            if not os.path.isfile(fn):
                raise KiPlotConfigurationError("Missing import file `{}`".format(fn))
        return fn, is_internal

    def _parse_import(self, imp, name, apply=True, depth=0):
        """ Get imports """
        logger.debug("Parsing imports: {}".format(imp))
        depth += 1
        if depth > 20:
            raise KiPlotConfigurationError("Import depth greater than 20, make sure this isn't an infinite loop")
        if not isinstance(imp, list):
            raise KiPlotConfigurationError("Incorrect `import` section (must be a list)")
        # Import the files
        dir_name = os.path.dirname(os.path.abspath(name))
        all_collected = CollectedImports()
        for entry in imp:
            explicit_fils = explicit_vars = explicit_globals = explicit_pres = explicit_groups = False
            if isinstance(entry, str):
                is_external = True
                fn = entry
                outs = None
                filters = []
                vars = []
                globals = []
                pre = []
                groups = []
                explicit_outs = True
            elif isinstance(entry, dict):
                fn = outs = filters = vars = globals = pre = groups = None
                explicit_outs = is_external = False
                for k, v in entry.items():
                    if k == 'file':
                        if not isinstance(v, str):
                            raise KiPlotConfigurationError("`import.file` must be a string ({})".format(str(v)))
                        fn = v
                    elif k == 'is_external':
                        if not isinstance(v, bool):
                            raise KiPlotConfigurationError("`import.is_external` must be a true/false ({})".format(str(v)))
                        is_external = v
                    elif k == 'outputs':
                        outs = self._parse_import_items(k, fn, v)
                        explicit_outs = True
                    elif k == 'preflights':
                        pre = self._parse_import_items(k, fn, v)
                        explicit_pres = True
                    elif k == 'filters':
                        filters = self._parse_import_items(k, fn, v)
                        explicit_fils = True
                    elif k == 'variants':
                        vars = self._parse_import_items(k, fn, v)
                        explicit_vars = True
                    elif k in ['global', 'globals']:
                        globals = self._parse_import_items(k, fn, v)
                        explicit_globals = True
                    elif k == 'groups':
                        groups = self._parse_import_items(k, fn, v)
                        explicit_groups = True
                    else:
                        self._config_error_import(fn, "Unknown import entry `{}`".format(str(v)))
                if fn is None:
                    raise KiPlotConfigurationError("`import` entry without `file` ({})".format(str(entry)))
            else:
                raise KiPlotConfigurationError("`import` items must be strings or dicts ({})".format(str(entry)))
            fn, is_internal = self.check_import_file_name(dir_name, fn, is_external)
            fn_rel = os.path.relpath(fn)
            data = self.load_yaml(open(fn))
            if 'import' in data:
                # Do a recursive import
                imported = self._parse_import(data['import'], fn, apply=False, depth=depth)
            else:
                # Nothing to import, start fresh
                imported = CollectedImports()
            # Parse and filter all stuff, add them to all_collected
            # Outputs
            all_collected.outputs.extend(self._parse_import_outputs(outs, explicit_outs, fn_rel, data, imported))
            # Preflights
            all_collected.preflights.extend(self._parse_import_preflights(pre, explicit_pres, fn_rel, data, imported))
            # Filters
            all_collected.filters.update(self._parse_import_filters(filters, explicit_fils, fn_rel, data, imported,
                                         is_internal))
            # Variants
            all_collected.variants.update(self._parse_import_variants(vars, explicit_vars, fn_rel, data, imported,
                                          is_internal))
            # Globals
            update_dict(all_collected.globals, self._parse_import_globals(globals, explicit_globals, fn_rel, data, imported))
            # Groups
            all_collected.groups.update(self._parse_import_groups(groups, explicit_groups, fn_rel, data, imported))
        if apply:
            # This is the main import (not a recursive one) apply the results
            RegOutput.add_filters(all_collected.filters)
            self.configure_variants(all_collected.variants)
            RegOutput.add_variants(all_collected.variants)
            self.imported_globals = all_collected.globals
            BasePreFlight.add_preflights(all_collected.preflights)
            RegOutput.add_outputs(all_collected.outputs, fn_rel)
            RegOutput.add_groups(all_collected.groups, fn_rel)
        return all_collected

    def load_yaml(self, fstream):
        if GS.cli_defines:
            # Load the file to memory so we can preprocess it
            content = fstream.read()
            logger.debug('Applying preprocessor definitions')
            # Replace all
            for k, v in GS.cli_defines.items():
                key = '@'+k+'@'
                logger.debugl(2, '- Replacing {} -> {}'.format(key, v))
                content = content.replace(key, v)
            # Create an stream from the string
            fstream = io.StringIO(content)
        try:
            data = yaml.safe_load(fstream)
        except yaml.YAMLError as e:
            raise KiPlotConfigurationError("Error loading YAML "+str(e))
        # Accept `globals` for `global`
        if 'globals' in data and 'global' not in data:
            data['global'] = data['globals']
            del data['globals']
        return data

    def _check_invalid_in_kibot(self, main_sec):
        defined_in_kibot = set(main_sec.keys())
        invalid_in_kibot = defined_in_kibot-VALID_KIBOT_SEC
        for k in invalid_in_kibot:
            raise KiPlotConfigurationError('Unknown option `{}` in kibot/kiplot.'.format(k))

    def read(self, fstream):
        """
        Read a file object into a config object

        :param fstream: file stream of a config YAML file
        """
        data = self.load_yaml(fstream)
        # Analyze the version
        # Currently just checks for v1
        v1 = data.get('kiplot', None)
        v2 = data.get('kibot', None)
        if v1 and v2:
            raise KiPlotConfigurationError("Use `kibot` or `kiplot` but not both.")
        if not v1 and not v2:
            raise KiPlotConfigurationError("YAML config needs `kibot.version`.")
        main_sec = v1 or v2
        self._check_version(main_sec)
        self._check_globals_priority(main_sec)
        self._check_invalid_in_kibot(main_sec)
        # Look for imports
        v1 = data.get('import', None)
        if v1:
            self._parse_import(v1, fstream.name)
        # Look for globals
        # If no globals defined initialize them with default values
        self._parse_global(data.get('global', {}))
        # Look for filters
        v1 = data.get('filters', None)
        if v1:
            RegOutput.add_filters(self._parse_filters(v1))
        # Look for variants
        v1 = data.get('variants', None)
        if v1:
            variants = self._parse_variants(v1)
            self.configure_variants(variants)
            RegOutput.add_variants(variants)
        # Solve the global variant
        if GS.global_variant:
            try:
                GS.solved_global_variant = RegOutput.check_variant(GS.global_variant)
            except KiPlotConfigurationError as e:
                raise KiPlotConfigurationError("In global section: "+str(e))
        # Look for preflights
        v1 = data.get('preflight', None)
        if v1:
            BasePreFlight.add_preflights(self._parse_preflights(v1))
        # Look for outputs
        v1 = data.get('outputs', None)
        if v1:
            RegOutput.add_outputs(self._parse_outputs(v1))
        # Look for groups
        v1 = data.get('groups', None)
        if v1:
            RegOutput.add_groups(self._parse_groups(v1))
        # Report invalid sections (the first we find)
        defined_sections = set(data.keys())
        invalid_sections = defined_sections-VALID_SECTIONS
        for k in invalid_sections:
            raise KiPlotConfigurationError('Unknown section `{}` in config.'.format(k))
        # Ok, now we have all the outputs loaded, so we can apply the disable_run_by_default
        for name in self.no_run_by_default:
            o = RegOutput.get_output(name)
            if o:
                o.run_by_default = False
                logger.debug("Disabling the default run for `{}`".format(o))

        return RegOutput.get_outputs()


def trim(docstring):
    """ PEP 257 recommended trim for __doc__ """
    if docstring is None:
        return []
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    # while trimmed and not trimmed[-1]:
    #     trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return trimmed


def print_output_options(name, cl, indent):
    ind_str = indent*' '
    obj = cl()
    num_opts = 0
    for k, v in sorted(obj.get_attrs_gen(), key=lambda x: not obj.is_basic_option(x[0])):
        if k == 'type' and indent == 2:
            # Type is fixed for an output
            continue
        if not num_opts:
            # We found one, put the title
            print(ind_str+'* Valid keys:')
        help, alias, is_alias = obj.get_doc(k)
        is_basic = False
        if help and help[0] == '*':
            help = help[1:]
            is_basic = True
        if is_alias:
            help = 'Alias for '+alias
            entry = '  - *{}*: '
        elif is_basic:
            entry = '  - **`{}`**: '
        else:
            entry = '  - `{}`: '
        if help is None:
            help = 'Undocumented'
            logger.error('Undocumented option: `{}`'.format(k))
        lines = help.split('\n')
        preface = ind_str+entry.format(k)
        clines = len(lines)
        print('{}{}{}'.format(preface, lines[0].strip(), '.' if clines == 1 else ''))
        ind_help = len(preface)*' '
        for ln in range(1, clines):
            text = lines[ln].strip()
            # Dots at the beginning are replaced by spaces.
            # Used to keep indentation.
            if text[0] == '.':
                for i in range(1, len(text)):
                    if text[i] != '.':
                        break
                text = ' '*i+text[i:]
            print('{}{}'.format(ind_help+text, '.' if ln+1 == clines else ''))
        num_opts = num_opts+1
        if isinstance(v, type):
            print_output_options('', v, indent+4)
    # if num_opts == 0:
    #     print(ind_str+'  - No available options')


def print_one_out_help(details, n, o):
    lines = trim(o.__doc__)
    if len(lines) == 0:
        lines = ['Undocumented', 'No description']
    if details:
        print('* '+lines[0])
        print('  * Type: `{}`'.format(n))
        print('  * Description: '+lines[1])
        for ln in range(2, len(lines)):
            print('                 '+lines[ln])
        print_output_options(n, o, 2)
    else:
        print('* {} [{}]'.format(lines[0], n))


def print_outputs_help(details=False):
    outs = RegOutput.get_registered()
    logger.debug('{} supported outputs'.format(len(outs)))
    print('Supported outputs:')
    if details:
        print('\nNotes:')
        print('1. Most relevant options are listed first and in **bold**. '
              'Which ones are more relevant is quite arbitrary, comments are welcome.')
        print('2. Aliases are listed in *italics*.')
    for n, o in OrderedDict(sorted(outs.items())).items():
        if details:
            print()
        print_one_out_help(details, n, o)


def print_output_help(name):
    if not RegOutput.is_registered(name):
        logger.error('Unknown output type `{}`, try --help-list-outputs'.format(name))
        exit(EXIT_BAD_ARGS)
    print_one_out_help(True, name, RegOutput.get_class_for(name))


def print_preflights_help():
    prefs = BasePreFlight.get_registered()
    logger.debug('{} supported preflights'.format(len(prefs)))
    print('Supported preflight options:\n')
    for n, o in OrderedDict(sorted(prefs.items())).items():
        help, options = o.get_doc()
        if help is None:
            help = 'Undocumented'
        print('- `{}`: {}.'.format(n, help.strip()))
        if options:
            print_output_options(n, options, 2)


def print_variants_help():
    from .var_base import BaseVariant
    vars = BaseVariant.get_registered()
    logger.debug('{} supported variants'.format(len(vars)))
    print('Supported variants:\n')
    for n, o in OrderedDict(sorted(vars.items())).items():
        help = o.__doc__
        if help is None:
            help = 'Undocumented'
        print('- `{}`: {}.'.format(n, help.strip()))
        print_output_options(n, o, 2)


def print_filters_help():
    filters = RegFilter.get_registered()
    logger.debug('{} supported filters'.format(len(filters)))
    print('Supported filters:\n')
    for n, o in OrderedDict(sorted(filters.items())).items():
        help = o.__doc__
        if help is None:
            help = 'Undocumented'
        print('- {}: {}.'.format(n, help.strip()))
        print_output_options(n, o, 2)


def print_global_options_help():
    print_output_options('Global options', GS.class_for_global_opts, 2)


def quoted(val):
    if "'" in val:
        return '"{}"'.format(val)
    return "'{}'".format(val)


def print_example_options(f, cls, name, indent, po, is_list=False):
    ind_str = indent*' '
    obj = cls()
    first = True
    if po:
        obj.read_vals_from_po(po)
    for k, _ in obj.get_attrs_gen():
        help, alias, is_alias = obj.get_doc(k, no_basic=True)
        if is_alias:
            f.write(ind_str+'# `{}` is an alias for `{}`\n'.format(k, alias))
            continue
        if help:
            help_lines = help.split('\n')
            for hl in help_lines:
                # Dots at the beginning are replaced by spaces.
                # Used to keep indentation.
                hl = hl.strip()
                if hl[0] == '.':
                    for i in range(1, len(hl)):
                        if hl[i] != '.':
                            break
                    hl = ' '*i+hl[i:]
                f.write(ind_str+'# '+hl+'\n')
        example_attr = '_'+k+'_example'
        if hasattr(obj, example_attr):
            val = getattr(obj, example_attr)
        else:
            val = getattr(obj, k)
        if isinstance(val, str):
            val = quoted(val)
        elif isinstance(val, bool):
            val = str(val).lower()
        if isinstance(val, type):
            if val.__name__ == 'Optionable' and help and '=' in help_lines[0]:
                # Get the text after =
                txt = help_lines[0].split('=')[1]
                # Get the text before the space, without the ]
                txt = txt.split()[0][:-1]
                f.write(ind_str+'{}: {}\n'.format(k, txt))
            elif val.get_default():
                f.write(ind_str+'{}: {}\n'.format(k, val.get_default()))
            else:
                if is_list and first:
                    k = '- '+k
                f.write(ind_str+'{}:\n'.format(k))
                extra_indent = 2 if not is_list else 4
                print_example_options(f, val, '', indent+extra_indent, None, help and 'list(dict' in help_lines[0])
                if is_list and first:
                    ind_str += '  '
                    first = False
        else:
            if is_list and first:
                k = '- '+k
            if val is None:
                val = 'null'
            f.write(ind_str+'{}: {}\n'.format(k, val))
            if is_list and first:
                ind_str += '  '
                first = False
    return obj


def create_example(pcb_file, out_dir, copy_options, copy_expand):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    fname = os.path.join(out_dir, EXAMPLE_CFG)
    if os.path.isfile(fname):
        logger.error(fname+" already exists, won't overwrite")
        exit(WONT_OVERWRITE)
    with open(fname, 'w') as f:
        logger.info('Creating {} example configuration'.format(fname))
        f.write("# ATTENTION! THIS ISN'T A FULLY FUNCTIONAL EXAMPLE.\n")
        f.write("# You should take portions of this example and edit the options to make\n")
        f.write("# them suitable for your use.\n")
        f.write("# This file is useful to know all the available options.\n")
        f.write('kibot:\n  version: 1\n')
        # Preflights
        f.write('\npreflight:\n')
        prefs = BasePreFlight.get_registered()
        for n, o in OrderedDict(sorted(prefs.items())).items():
            if o.__doc__:
                lines = trim(o.__doc__.rstrip()+'.')
                for ln in lines:
                    f.write('  # '+ln.rstrip()+'\n')
            example = o.get_example()
            if not example.startswith("\n"):
                example = ' '+example
            f.write('  {}:{}\n'.format(n, example))
        # Outputs
        outs = RegOutput.get_registered()
        f.write('\noutputs:\n')
        # List of layers
        po = None
        layers = 'all'
        if pcb_file:
            # We have a PCB to take as reference
            board = GS.load_board(pcb_file)
            if copy_options or copy_expand:
                # Layers and plot options from the PCB
                layers = 'selected'
                po = board.GetPlotOptions()
        for n, cls in OrderedDict(sorted(outs.items())).items():
            lines = trim(cls.__doc__)
            if len(lines) == 0:
                lines = ['Undocumented', 'No description']
            f.write('  # '+lines[0].rstrip()+':\n')
            for ln in range(2, len(lines)):
                f.write('  # '+lines[ln].rstrip()+'\n')
            f.write("  - name: '{}_example'\n".format(n))
            f.write("    comment: {}\n".format(quoted(lines[1])))
            f.write("    type: '{}'\n".format(n))
            f.write("    dir: 'Example/{}_dir'\n".format(n))
            f.write("    options:\n")
            obj = cls()
            print_example_options(f, obj.options, n, 6, po)
            if 'layers' in obj.__dict__:
                if copy_expand:
                    f.write('    layers:\n')
                    layers = obj.layers.solve(layers)
                    for layer in layers:
                        f.write("      - layer: '{}'\n".format(layer.layer))
                        f.write("        suffix: '{}'\n".format(layer.suffix))
                        if layer.description:
                            f.write("        description: '{}'\n".format(layer.description))
                else:
                    f.write('    layers: {}\n'.format(layers))


def global2human(name):
    return '`'+name+'`' if name != 'global' else 'general use'


class MyEncoder(json.JSONEncoder):
    """ Simple JSON encoder for objects """
    def default(self, o):
        return o.__dict__


def print_dep_comments(dep):
    if len(dep.comments) == 1:
        print('- Note: '+dep.comments[0])
    elif len(dep.comments) > 1:
        print('- Notes:')
        for comment in dep.comments:
            print('  - '+comment)


def compose_version(version, max_version):
    ver = ' v'+'.'.join(map(str, version)) if version else ''
    ver += ' (<'+'.'.join(map(str, max_version))+')' if max_version else ''
    return ver


def print_needed(needed):
    if needed:
        if len(needed) == 1:
            if needed[0] == 'general use':
                print('- Mandatory')
            else:
                print('- Mandatory for '+needed[0])
        else:
            print('- Mandatory for: '+', '.join(sorted(needed)))


def print_dependencies(markdown=True, jsn=False):
    # Compute the importance of each dependency
    for dep in RegDependency.get_registered().values():
        importance = 0
        for r in dep.roles:
            local = r.output != 'global'
            if r.mandatory:
                importance += LOCAL_MANDATORY if local else GLOBAL_MANDATORY
            else:
                importance += LOCAL_OPTIONAL if local else GLOBAL_OPTIONAL
        dep.importance = importance
    # The JSON output is just a dump
    if jsn:
        print(json.dumps(RegDependency.get_registered(), cls=MyEncoder, indent=4, sort_keys=True))
        return
    # Now print them sorted by importance (and by name as a second criteria)
    for name, dep in sorted(sorted(RegDependency.get_registered().items(), key=lambda x: x[0].lower()),   # noqa C414
                            key=lambda x: x[1].importance, reverse=True):
        deb = ''
        if markdown:
            dtype = PY_LOGO if dep.is_python else TOOL_LOGO
            is_pypi_dep = PYPI_LOGO if dep.pypi_name.lower() in __pypi_deps__ else ''
            has_dowloader = ' '+AUTO_DOWN if dep.downloader is not None else ''
            if dep.is_python:
                url = 'https://pypi.org/project/{}/'.format(name)
                if is_pypi_dep:
                    is_pypi_dep = ' [{}]({})'.format(is_pypi_dep, url)
            else:
                url = dep.url
            name = '[**{}**]({})'.format(name, url)
            dtype = ' [{}]({})'.format(dtype, url)
            if dep.in_debian:
                deb = ' [{}](https://packages.debian.org/bullseye/{})'.format(DEB_LOGO, dep.deb_package)
        else:
            dtype = ' (Python module)' if dep.is_python else ' (Tool)'
            is_pypi_dep = ' (PyPi dependency)' if dep.pypi_name.lower() in __pypi_deps__ else ''
            has_dowloader = ' (Auto-download)' if dep.downloader is not None else ''
            if dep.in_debian:
                deb = ' (Debian: {})'.format(dep.deb_package)
        needed = []
        optional = []
        version = None
        max_version = None
        for r in dep.roles:
            if r.mandatory:
                needed.append(global2human(r.output))
            else:
                optional.append(r)
            if r.version and (version is None or r.version > version):
                version = r.version
            if r.max_version and (max_version is None or r.max_version < max_version):
                max_version = r.max_version
        ver = compose_version(version, max_version)
        print(name+ver+dtype+is_pypi_dep+deb+has_dowloader)
        print_needed(needed)
        if optional:
            if len(optional) == 1:
                o = optional[0]
                desc = o.desc[0].lower()+o.desc[1:]
                print('- Optional to {} for {}'.format(desc, global2human(o.output)))
            else:
                print('- Optional to:')
                for o in optional:
                    ver = ''
                    if o.version:
                        ver = ' (v'+'.'.join(map(str, o.version))+')'
                    print('  - {} for {}{}'.format(o.desc, global2human(o.output), ver))
        print_dep_comments(dep)
        print()
