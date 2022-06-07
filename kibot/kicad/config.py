# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
KiCad configuration classes.
Reads the KiCad's configuration files.
In particular:
- kicad_common to know about the 'environment' variables
- The `sym-lib-table` files to map library aliases

Notes about coverage:
I'm excluding all the Darwin and Windows code from coverage.
I'm not even sure the values are correct.
"""
import os
import re
import sys
import json
from io import StringIO
from glob import glob
from shutil import copy2
import platform
import sysconfig
from ..gs import GS
from .. import log
from ..misc import W_NOCONFIG, W_NOKIENV, W_NOLIBS, W_NODEFSYMLIB, MISSING_WKS

# Check python version to determine which version of ConfirParser to import
if sys.version_info.major >= 3:
    import configparser as ConfigParser
else:  # pragma: no cover (Py2)
    # For future Python 2 support
    import ConfigParser

logger = log.get_logger()
SYM_LIB_TABLE = 'sym-lib-table'
KICAD_COMMON = 'kicad_common'


class KiConfError(Exception):
    def __init__(self, msg, file, lnum, line):
        super().__init__()
        self.line = lnum
        self.file = file
        self.msg = msg
        self.code = line


def un_quote(val):
    """ Remove optional quotes """
    if val[0] == '"':
        val.replace('\"', '"')
        val = val[1:-1]
    return val


def expand_env(val, env, extra_env, used_extra=None):
    """ Expand KiCad environment variables """
    if used_extra is None:
        used_extra = [False]
    used_extra[0] = False
    for var in re.findall(r'\$\{(\S+?)\}', val):
        if var in env:
            val = val.replace('${'+var+'}', env[var])
        elif var in extra_env:
            val = val.replace('${'+var+'}', extra_env[var])
            used_extra[0] = True
        else:
            logger.error('Unable to expand `{}` in `{}`'.format(var, val))
    return val


class LibAlias(object):
    """ An entry for the symbol libs table """
    libs_re = re.compile(r'\(name\s+(\S+|"(?:[^"]|\\")+")\)\s*\(type\s+(\S+|"(?:[^"]|\\")+")\)'
                         r'\s*\(uri\s+(\S+|"(?:[^"]|\\")+")\)\s*\(options\s+(\S+|"(?:[^"]|\\")+")\)'
                         r'\s*\(descr\s+(\S+|"(?:[^"]|\\")+")\)')

    def __init__(self):
        super().__init__()
        self.name = None
        self.legacy = True
        self.uri = None
        self.options = None
        self.descr = None

    @staticmethod
    def parse(options, cline, env, extra_env):
        m = LibAlias.libs_re.match(options)
        if not m:
            raise KiConfError('Malformed lib entry', SYM_LIB_TABLE, cline, options)
        lib = LibAlias()
        lib.name = un_quote(m.group(1))
        lib.legacy = m.group(2) == 'Legacy'
        lib.uri = os.path.abspath(expand_env(un_quote(m.group(3)), env, extra_env))
        lib.options = un_quote(m.group(4))
        lib.descr = un_quote(m.group(5))
        return lib

    def __str__(self):
        if not self.name:
            return 'unnamed LibAlias'
        return '`'+self.name+'` -> `'+self.uri+'`'


class KiConf(object):
    """ Class to load and hold all KiCad configuration """
    loaded = False
    config_dir = None
    dirname = None
    sym_lib_dir = None
    template_dir = None
    footprint_dir = None
    kicad_env = {}
    lib_aliases = {}

    def __init__(self):
        raise AssertionError("KiConf is fully static, no instances allowed")

    def init(fname):
        """ fname is the base project name, any extension is allowed.
            So it can be the main schematic, the PCB or the project. """
        if KiConf.loaded:
            return
        KiConf.dirname = os.path.dirname(fname)
        KiConf.kicad_env['KIPRJMOD'] = KiConf.dirname
        KiConf.load_kicad_common()
        KiConf.load_all_lib_aliases()
        KiConf.loaded = True

    def find_kicad_common():
        """ Looks for kicad_common config file.
            Returns its name or None. """
        cfg = ''
        if GS.kicad_conf_path:
            cfg = os.path.join(GS.kicad_conf_path, KICAD_COMMON)
            if GS.ki6():
                cfg += '.json'
            if os.path.isfile(cfg):
                return cfg
        logger.warning(W_NOCONFIG + 'Unable to find KiCad configuration file ({})'.format(cfg))
        return None

    def _guess_kicad_data_dir(data_dir):
        """ Tries to figure out where libraries are.
            Only used if we failed to find the kicad_common file. """
        system = platform.system()
        share = os.path.join('share', GS.kicad_dir, data_dir)
        if system == 'Linux':
            scheme_names = sysconfig.get_scheme_names()
            # Try in local dir
            if 'posix_user' in scheme_names:
                dir = os.path.join(sysconfig.get_path('data', 'posix_user'), share)
                if os.path.isdir(dir):
                    return dir
            # Try at system level
            if 'posix_prefix' in scheme_names:
                dir = os.path.join(sysconfig.get_path('data', 'posix_prefix'), share)
                if os.path.isdir(dir):
                    return dir
        elif system == 'Darwin':  # pragma: no cover (Darwin)
            app_data = os.path.join('Library', 'Application Support', GS.kicad_dir, data_dir)
            home = os.environ.get('HOME')
            if home:
                dir = os.path.join(home, app_data)
                if os.path.isdir(dir):
                    return dir
            dir = os.path.join('/', app_data)
            if os.path.isdir(dir):
                return dir
        elif system == 'Windows':  # pragma: no cover (Windows)
            dir = os.path.join('C:', 'Program Files', 'KiCad', share)
            if os.path.isdir(dir):
                return dir
            dir = os.path.join('C:', 'KiCad', share)
            if os.path.isdir(dir):
                return dir
            username = os.environ.get('username')
            dir = os.path.join('C:', 'Users', username, 'Documents', 'KiCad', data_dir)
            if os.path.isdir(dir):
                return dir
        return None

    def guess_symbol_dir():
        if GS.ki5():
            order = ['library', 'symbols']
        else:
            order = ['symbols', 'library']
        guess = KiConf._guess_kicad_data_dir(order[0])
        if guess is None:
            guess = KiConf._guess_kicad_data_dir(order[1])
        return guess

    def guess_footprint_dir():
        if GS.ki5():
            order = ['modules', 'footprints']
        else:
            order = ['footprints', 'modules']
        guess = KiConf._guess_kicad_data_dir(order[0])
        if guess is None:
            guess = KiConf._guess_kicad_data_dir(order[1])
        return guess

    def guess_template_dir():
        return KiConf._guess_kicad_data_dir('template')

    def guess_3d_dir():
        modules3d = os.path.join('modules', 'packages3d')
        if GS.ki5():
            order = [modules3d, '3dmodels']
        else:
            order = ['3dmodels', modules3d]
        guess = KiConf._guess_kicad_data_dir(order[0])
        if guess is None:
            guess = KiConf._guess_kicad_data_dir(order[1])
        return guess

    def guess_user_template_dir():
        system = platform.system()
        if system == 'Linux':
            home = os.environ.get('HOME')
            if home is None:
                return None
            if GS.ki6():
                name = os.path.join(home, '.local', 'share', 'kicad', '6.0', 'template')
                if os.path.isdir(name):
                    return name
            name = os.path.join(home, 'kicad', 'template')
            if os.path.isdir(name):
                return name
            return None
        elif system == 'Darwin':  # pragma: no cover (Darwin)
            home = os.environ.get('HOME')
            if home is None:
                return None
            name = os.path.join(home, 'Documents', 'kicad', 'template')
            if os.path.isdir(name):
                return name
            return None
        elif system == 'Windows':  # pragma: no cover (Windows)
            username = os.environ.get('username')
            dir = os.path.join('C:', 'Documents and Settings', username, 'My Documents', 'kicad', 'template')
            if os.path.isdir(dir):
                return dir
            dir = os.path.join('C:', 'Users', username, 'Documents', 'kicad', 'template')
            if os.path.isdir(dir):
                return dir
            return None

    def guess_3rd_dir():
        home = os.environ.get('HOME')
        if home is None:
            return None
        return os.path.join(home, '.local', 'share', 'kicad', '6.0', '3rdparty')

    def load_ki5_env(cfg):
        """ Environment vars from KiCad 5 configuration """
        # Load the "environment variables"
        with open(cfg, 'rt') as f:
            buf = f.read()
        io_buf = StringIO('[Default]\n'+buf)
        cf = ConfigParser.RawConfigParser(allow_no_value=True)
        cf.optionxform = str
        if sys.version_info.major >= 3:
            cf.read_file(io_buf, cfg)
        else:  # pragma: no cover (Py2)
            cf.readfp(io_buf, cfg)
        if 'EnvironmentVariables' not in cf.sections():
            logger.warning(W_NOKIENV + 'KiCad config without EnvironmentVariables section')
        else:
            for k, v in cf.items('EnvironmentVariables'):
                if GS.debug_level > 1:
                    logger.debug('- KiCad var: {}="{}"'.format(k, v))
                KiConf.kicad_env[k] = v

    def load_ki6_env(cfg):
        """ Environment vars from KiCad 6 configuration """
        # Notes about KiCad 6 environment vars:
        # 1) KiCad has some hardcoded internal values
        # 2) Only the values that the user modifies are stored in the config file
        # 3) Any value defined in the environment will have priority over internal definitions
        # It means that we currently don't know the real value unless the user modifies it or defines in the env
        with open(cfg, 'rt') as f:
            data = json.load(f)
        if "environment" in data and 'vars' in data['environment'] and (data['environment']['vars'] is not None):
            for k, v in data['environment']['vars'].items():
                if GS.debug_level > 1:
                    logger.debug('- KiCad var: {}="{}"'.format(k, v))
                KiConf.kicad_env[k] = v
        else:
            logger.warning(W_NOKIENV + 'KiCad config without environment.vars section')

    def _look_env_var(base_name, old, only_old, ki6_diff, no_dir):
        """ Looks for a KiCad variable definition.
            First in the OS environment, then in the config.
            Sync the other source. """
        if not no_dir:
            base_name += '_DIR'
        names = []
        if GS.ki6() and ki6_diff:
            # KiCad 6 specific name goes first when using KiCad 6
            names.append('KICAD6_'+base_name)
        # KiCad 5 names, allowed even when using KiCad 6
        if not only_old:
            # A KICAD_* is valid
            names.append('KICAD_'+base_name)
        if old:
            # A specific legacy name
            names.append(old)
        ret_val = None
        # Look for the above names
        # The first we find is the one we use, but we export all the ones we found
        for n in names:
            val = None
            # OS environment has more priority
            if n in os.environ:
                val = os.environ[n]
                KiConf.kicad_env[n] = val
                logger.debug('Using {}="{}" (from environment)'.format(n, val))
            # Then the file
            elif n in KiConf.kicad_env:
                val = KiConf.kicad_env[n]
                os.environ[n] = val
                logger.debug('Using {}="{}" (from KiCad config)'.format(n, val))
            if val is not None and ret_val is None:
                ret_val = val
        return ret_val

    def _set_env_var(base_name, val, ki6_diff, no_dir):
        """ Sets the environment and the internal list """
        if not no_dir:
            base_name += '_DIR'
        if GS.ki6() and ki6_diff:
            name = 'KICAD6_'+base_name
        else:
            name = 'KICAD_'+base_name
        KiConf.kicad_env[name] = val
        os.environ[name] = val
        logger.debug('Using {}="{}" (guessed)'.format(name, val))

    def _solve_var(name, member, desc, guesser, old=None, only_old=False, ki6_diff=True, only_k6=False, no_dir=False):
        if only_k6 and GS.ki5():
            return
        val = KiConf._look_env_var(name, old, only_old, ki6_diff, no_dir)
        if val is not None:
            setattr(KiConf, member, val)
        else:
            val = guesser()
            if val:
                setattr(KiConf, member, val)
                KiConf._set_env_var(name, val, ki6_diff, no_dir)
                if old:
                    KiConf.kicad_env[old] = val
                    os.environ[old] = val
            else:
                logger.warning(W_NOLIBS + 'Unable to find KiCad '+desc)

    def load_kicad_common():
        # Try to figure out KiCad configuration file
        cfg = KiConf.find_kicad_common()
        if cfg and os.path.isfile(cfg):
            # Get the environment variables
            logger.debug('Reading KiCad config from `{}`'.format(cfg))
            KiConf.config_dir = os.path.dirname(cfg)
            if GS.ki5():
                # All environment vars should be here
                KiConf.load_ki5_env(cfg)
            else:
                # Only the user defined environment vars are here
                KiConf.load_ki6_env(cfg)
        # Now make sure we have all the needed variables
        KiConf._solve_var('SYMBOL', 'sym_lib_dir', 'libraries', KiConf.guess_symbol_dir)
        KiConf._solve_var('TEMPLATE', 'template_dir', 'templates', KiConf.guess_template_dir)
        KiConf._solve_var('USER_TEMPLATE', 'user_template_dir', 'user templates', KiConf.guess_user_template_dir,
                          ki6_diff=False)
        KiConf._solve_var('FOOTPRINT', 'footprint_dir', 'footprints', KiConf.guess_footprint_dir, old='KISYSMOD')
        KiConf._solve_var('3DMODEL', 'models_3d_dir', '3D models', KiConf.guess_3d_dir, old='KISYS3DMOD', only_old=True)
        KiConf._solve_var('3RD_PARTY', 'party_3rd_dir', '3rd party', KiConf.guess_3rd_dir, only_k6=True, no_dir=True)
        # Export the rest. KiCad2Step needs them
        for k, v in KiConf.kicad_env.items():
            if k not in os.environ:
                os.environ[k] = v
                logger.debug('Exporting {}="{}"'.format(k, v))

    def load_lib_aliases(fname):
        if not os.path.isfile(fname):
            return False
        logger.debug('Loading symbols lib table `{}`'.format(fname))
        with open(fname, 'rt') as f:
            line = f.readline().strip()
            if line != '(sym_lib_table':
                raise KiConfError('Symbol libs table missing signature', SYM_LIB_TABLE, 1, line)
            line = f.readline()
            cline = 2
            while line and line[0] != ')':
                m = re.match(r'\s*\(lib\s*(.*)\)', line)
                if m:
                    alias = LibAlias.parse(m.group(1), cline, KiConf.kicad_env, {})
                    if GS.debug_level > 1:
                        logger.debug('- Adding lib alias '+str(alias))
                    KiConf.lib_aliases[alias.name] = alias
                else:
                    raise KiConfError('Unknown symbol table entry', SYM_LIB_TABLE, cline, line)
                line = f.readline()
                cline += 1
        return True

    def load_all_lib_aliases():
        # Load the default symbol libs table.
        # This is the list of libraries enabled by the user.
        loaded = False
        if KiConf.config_dir:
            conf_dir = KiConf.config_dir
            if 'KICAD_CONFIG_HOME' in KiConf.kicad_env:
                # KiCad 5 unintentionally allows it, is a bug, and won't be fixed:
                # https://forum.kicad.info/t/kicad-config-home-inconsistencies-and-detail/26875
                conf_dir = KiConf.kicad_env['KICAD_CONFIG_HOME']
                logger.debug('Redirecting symbols lib table to '+conf_dir)
            loaded = KiConf.load_lib_aliases(os.path.join(conf_dir, SYM_LIB_TABLE))
        if not loaded and 'KICAD_TEMPLATE_DIR' in KiConf.kicad_env:
            loaded = KiConf.load_lib_aliases(os.path.join(KiConf.kicad_env['KICAD_TEMPLATE_DIR'], SYM_LIB_TABLE))
        if not loaded:
            logger.warning(W_NODEFSYMLIB + 'Missing default symbol library table')
            # No default symbol libs table, try to create one
            if KiConf.sym_lib_dir:
                for f in glob(os.path.join(KiConf.sym_lib_dir, '*.lib')):
                    alias = LibAlias()
                    alias.name = os.path.splitext(os.path.basename(f))[0]
                    alias.uri = f
                    if GS.debug_level > 1:
                        logger.debug('Detected lib alias '+str(alias))
                    KiConf.lib_aliases[alias.name] = alias
        # Load the project's table
        KiConf.load_lib_aliases(os.path.join(KiConf.dirname, SYM_LIB_TABLE))

    def fix_page_layout_k6_key(key, data, dest_dir):
        if key in data:
            section = data[key]
            pl = section.get('page_layout_descr_file', None)
            if pl:
                fname = KiConf.expand_env(pl)
                if os.path.isfile(fname):
                    dest = os.path.join(dest_dir, key+'.kicad_wks')
                    logger.debug('Copying {} -> {}'.format(fname, dest))
                    copy2(fname, dest)
                    data[key]['page_layout_descr_file'] = dest
                    return dest
                else:
                    logger.error('Missing page layout file: '+fname)
                    exit(MISSING_WKS)
        return None

    def fix_page_layout_k6(project, dry):
        # Get the current definitions
        dest_dir = os.path.dirname(project)
        with open(project, 'rt') as f:
            pro_text = f.read()
        data = json.loads(pro_text)
        layouts = [None, None]
        if not dry:
            layouts[1] = KiConf.fix_page_layout_k6_key('pcbnew', data, dest_dir)
            layouts[0] = KiConf.fix_page_layout_k6_key('schematic', data, dest_dir)
            with open(project, 'wt') as f:
                f.write(json.dumps(data, sort_keys=True, indent=2))
        else:
            aux = data.get('schematic', None)
            if aux:
                layouts[0] = KiConf.expand_env(aux.get('page_layout_descr_file', None))
            aux = data.get('pcbnew', None)
            if aux:
                layouts[1] = KiConf.expand_env(aux.get('page_layout_descr_file', None))
        return layouts

    def fix_page_layout_k5(project, dry):
        order = 1
        dest_dir = os.path.dirname(project)
        with open(project, 'rt') as f:
            lns = f.readlines()
        is_pcb_new = False
        layouts = [None, None]
        for c, line in enumerate(lns):
            if line.startswith('[pcbnew]'):
                is_pcb_new = True
            if line.startswith('[schematic'):
                is_pcb_new = False
            if line.startswith('PageLayoutDescrFile='):
                fname = line[20:].strip()
                if fname:
                    fname = KiConf.expand_env(fname)
                    if os.path.isfile(fname):
                        dest = os.path.join(dest_dir, str(order)+'.kicad_wks')
                        if not dry:
                            copy2(fname, dest)
                            layouts[is_pcb_new] = dest
                        else:
                            layouts[is_pcb_new] = fname
                        order = order+1
                    else:
                        logger.error('Missing page layout file: '+fname)
                        exit(MISSING_WKS)
                else:
                    dest = ''
                lns[c] = 'PageLayoutDescrFile='+dest+'\n'
        if not dry:
            with open(project, 'wt') as f:
                lns = f.writelines(lns)
        return layouts

    def fix_page_layout(project, dry=False):
        if not project:
            return None, None
        KiConf.init(GS.pcb_file)
        if GS.ki5():
            return KiConf.fix_page_layout_k5(project, dry)
        return KiConf.fix_page_layout_k6(project, dry)

    def expand_env(name, used_extra=None):
        if used_extra is None:
            used_extra = [False]
        if not name:
            return name
        return os.path.abspath(expand_env(un_quote(name), KiConf.kicad_env, GS.load_pro_variables(), used_extra))
