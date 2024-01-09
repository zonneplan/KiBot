# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from tempfile import NamedTemporaryFile
from .gs import GS
from .kiplot import run_command
from .out_base import VariantOptions
from .pre_base import BasePreFlight
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class AnyDiffOptions(VariantOptions):
    def __init__(self):
        with document:
            self.zones = 'global'
            """ [global,fill,unfill,none] How to handle PCB zones. The default is *global* and means that we
                fill zones if the *check_zone_fills* preflight is enabled. The *fill* option always forces
                a refill, *unfill* forces a zone removal and *none* lets the zones unchanged.
                Be careful with the *keep_generated* option when changing this setting """
        super().__init__()
        self._expand_id = 'diff'
        self._expand_ext = 'pdf'
        self._kiri_mode = False

    def add_zones_ops(self, cmd):
        if self.zones == 'global':
            if BasePreFlight.get_option('check_zone_fills'):
                cmd.extend(['--zones', 'fill'])
        elif self.zones == 'fill':
            cmd.extend(['--zones', 'fill'])
        elif self.zones == 'unfill':
            cmd.extend(['--zones', 'unfill'])

    def add_to_cache(self, name, hash):
        cmd = [self.command, '--no_reader', '--only_cache', '--old_file_hash', hash, '--cache_dir', self.cache_dir]
        if self._kiri_mode:
            cmd.append('--kiri_mode')
        self.add_zones_ops(cmd)
        if self.incl_file:
            cmd.extend(['--layers', self.incl_file])
        if not hasattr(self, 'only_first_sch_page') or not self.only_first_sch_page:
            cmd.append('--all_pages')
        if GS.debug_enabled:
            cmd.insert(1, '-'+'v'*GS.debug_level)
        cmd.extend([name, name])
        self.name_used_for_cache = name
        run_command(cmd)

    def run_git(self, cmd, cwd=None, just_raise=False):
        if cwd is None:
            cwd = self.repo_dir
        return run_command([self.git_command]+cmd, change_to=cwd, just_raise=just_raise)

    def git_dirty(self, file=None):
        ops = ['status', '--porcelain', '-uno']
        if file is not None:
            ops.append(file)
        return self.run_git(ops)

    def remove_git_worktree(self, name):
        logger.debug('Removing temporal checkout at '+name)
        self.run_git(['worktree', 'remove', '--force', name])

    def save_layers_incl(self, layers):
        self._solved_layers = layers
        logger.debug('Including layers:')
        with NamedTemporaryFile(mode='w', suffix='.lst', delete=False) as f:
            self.incl_file = f.name
            for la in layers:
                logger.debug('- {} ({})'.format(la.layer, la.id))
                f.write(str(la.id)+'\n')
        return self.incl_file
