# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
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
from io import StringIO
from glob import glob
import platform
import sysconfig
from ..gs import GS
from .. import log

# Check python version to determine which version of ConfirParser to import
if sys.version_info.major >= 3:
    import configparser as ConfigParser
else:  # pragma: no cover
    # For future Python 2 support
    import ConfigParser

logger = log.get_logger(__name__)
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


def expand_env(val, env):
    """ Expand KiCad environment variables """
    for var in re.findall(r'\$\{(\S+)\}', val):
        if var in env:
            val = val.replace('${'+var+'}', env[var])
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
    def parse(options, cline, env):
        m = LibAlias.libs_re.match(options)
        if not m:
            raise KiConfError('Malformed lib entry', SYM_LIB_TABLE, cline, options)
        lib = LibAlias()
        lib.name = un_quote(m.group(1))
        lib.legacy = m.group(2) == 'Legacy'
        lib.uri = os.path.abspath(expand_env(un_quote(m.group(3)), env))
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
    kicad_env = {}
    lib_aliases = {}

    def __init__(self):
        assert False, "KiConf is fully static, no instances allowed"

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
        # User option has the higher priority
        user_set = os.environ.get('KICAD_CONFIG_HOME')
        if user_set:
            cfg = os.path.join(user_set, KICAD_COMMON)
            if os.path.isfile(cfg):
                return cfg
        # XDG option is second
        xdg_set = os.environ.get('XDG_CONFIG_HOME')
        if xdg_set:
            cfg = os.path.join(xdg_set, 'kicad', KICAD_COMMON)
            if os.path.isfile(cfg):
                return cfg
        # Others depends on the OS
        system = platform.system()
        if system == 'Linux':
            # Linux: ~/.config/kicad/
            home = os.environ.get('HOME')
            if not home:
                logger.warning('Environment variable `HOME` not defined, using `/`')
                home = '/'
            cfg = os.path.join(home, '.config', 'kicad', KICAD_COMMON)
            if os.path.isfile(cfg):
                return cfg
        elif system == 'Darwin':  # pragma: no cover
            # MacOSX: ~/Library/Preferences/kicad/
            home = os.environ.get('HOME')
            if not home:
                logger.warning('Environment variable `HOME` not defined, using `/`')
                home = '/'
            cfg = os.path.join(home, 'Library', 'Preferences', 'kicad', KICAD_COMMON)
            if os.path.isfile(cfg):
                return cfg
        elif system == 'Windows':  # pragma: no cover
            # Windows: C:\Users\username\AppData\Roaming\kicad
            #      or  C:\Documents and Settings\username\Application Data\kicad
            username = os.environ.get('username')
            if not username:
                logger.warning('Unable to determine current user')
                return None
            cfg = os.path.join('C:', 'Users', username, 'AppData', 'Roaming', 'kicad', KICAD_COMMON)
            if os.path.isfile(cfg):
                return cfg
            cfg = os.path.join('C:', 'Documents and Settings', username, 'Application Data', 'kicad', KICAD_COMMON)
            if os.path.isfile(cfg):
                return cfg
        else:  # pragma: no cover
            logger.warning('Unsupported system `{}`'.format(system))
            return None
        logger.warning('Unable to find KiCad configuration file ({})'.format(cfg))
        return None

    def guess_symbol_dir():
        """ Tries to figure out where libraries are.
            Only used if we failed to find the kicad_common file. """
        dir = os.environ.get('KICAD_SYMBOL_DIR')
        if dir and os.path.isdir(dir):
            return dir
        system = platform.system()
        share = os.path.join('share', 'kicad', 'library')
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
        elif system == 'Darwin':  # pragma: no cover
            app_data = os.path.join('Library', 'Application Support', 'kicad', 'library')
            home = os.environ.get('HOME')
            if home:
                dir = os.path.join(home, app_data)
                if os.path.isdir(dir):
                    return dir
            dir = os.path.join('/', app_data)
            if os.path.isdir(dir):
                return dir
        elif system == 'Windows':  # pragma: no cover
            dir = os.path.join('C:', 'Program Files', 'KiCad', share)
            if os.path.isdir(dir):
                return dir
            dir = os.path.join('C:', 'KiCad', share)
            if os.path.isdir(dir):
                return dir
            username = os.environ.get('username')
            dir = os.path.join('C:', 'Users', username, 'Documents', 'KiCad', 'library')
            if os.path.isdir(dir):
                return dir
        return None

    def load_kicad_common():
        # Try to figure out KiCad configuration file
        cfg = KiConf.find_kicad_common()
        if cfg and os.path.isfile(cfg):
            logger.debug('Reading KiCad config from `{}`'.format(cfg))
            KiConf.config_dir = os.path.dirname(cfg)
            # Load the "environment variables"
            with open(cfg, 'rt') as f:
                buf = f.read()
            io_buf = StringIO('[Default]\n'+buf)
            cf = ConfigParser.RawConfigParser(allow_no_value=True)
            cf.optionxform = str
            cf.readfp(io_buf, cfg)
            if 'EnvironmentVariables' not in cf.sections():
                logger.warning('KiCad config without EnvironmentVariables section')
            else:
                for k, v in cf.items('EnvironmentVariables'):
                    if GS.debug_level > 1:
                        logger.debug('- KiCad var: {}="{}"'.format(k, v))
                    KiConf.kicad_env[k] = v
        if 'KICAD_SYMBOL_DIR' in KiConf.kicad_env:
            KiConf.sym_lib_dir = KiConf.kicad_env['KICAD_SYMBOL_DIR']
        else:
            sym_dir = KiConf.guess_symbol_dir()
            if sym_dir:
                KiConf.kicad_env['KICAD_SYMBOL_DIR'] = sym_dir
                KiConf.sym_lib_dir = sym_dir
                logger.debug('Detected KICAD_SYMBOL_DIR="{}"'.format(sym_dir))
            else:
                logger.warning('Unable to find KiCad libraries')

    def load_lib_aliases(fname):
        if not os.path.isfile(fname):
            return
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
                    alias = LibAlias.parse(m.group(1), cline, KiConf.kicad_env)
                    if GS.debug_level > 1:
                        logger.debug('- Adding lib alias '+str(alias))
                    KiConf.lib_aliases[alias.name] = alias
                else:
                    raise KiConfError('Unknown symbol table entry', SYM_LIB_TABLE, cline, line)
                line = f.readline()
                cline += 1

    def load_all_lib_aliases():
        # Load the default symbol libs table.
        # This is the list of libraries enabled by the user.
        if KiConf.config_dir:
            KiConf.load_lib_aliases(os.path.join(KiConf.config_dir, SYM_LIB_TABLE))
        else:
            logger.warning('Missing default symbol library table')
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
