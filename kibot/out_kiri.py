# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Salvador E. Tropea
# Copyright (c) 2022-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - name: KiCad PCB/SCH Diff
    version: 2.5.0
    role: mandatory
    github: INTI-CMNB/KiDiff
    command: kicad-diff.py
    pypi: kidiff
    downloader: pytool
    id: KiDiff
  - from: Git
    role: Compare with files in the repo
  - from: KiAuto
    role: Compare schematics
    version: 2.2.0
"""
import datetime
import pwd
import os
from shutil import copy2
from subprocess import CalledProcessError
from tempfile import mkdtemp, NamedTemporaryFile
from .error import KiPlotConfigurationError
from .gs import GS
from .kicad.color_theme import load_color_theme
from .kiplot import load_any_sch, run_command
from .layer import Layer
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
STASH_MSG = 'KiBot_Changes_Entry'
TOOLTIP_HTML = '<div>Commit: {hash}</br>Date: {dt}</br>Author: {author}</br>Description:</br>{desc}</div>'
# Icons for modified status
EMPTY_IMG = ('<span class="iconify" style="padding-left: 0px; padding-right: 0px; width: 14px; height: 14px; color: #ff0000;"'
             ' data-inline="false"; data-icon="bx:bx-x"></span>')
SCH_IMG = ('<span class="iconify" style="padding-left: 0px; padding-right: 0px; width: 14px; height: 14px; color: #A6E22E;"'
           ' data-inline="false"; data-icon="carbon:schematics"></span>')
PCB_IMG = ('<span class="iconify" style="padding-left: 0px; padding-right: 0px; width: 14px; height: 14px; color: #F92672;"'
           ' data-inline="false"; data-icon="codicon:circuit-board"></span>')
TXT_IMG = ('<span class="iconify" style="padding-left: 0px; padding-right: 0px; width: 14px; height: 14px; color: #888888;"'
           ' data-inline="false"; data-icon="bi:file-earmark-text"></span>')
HASH_LOCAL = '_local_'


def get_cur_user():
    try:
        name = pwd.getpwuid(os.geteuid())[4]
        return name.split(',')[0]
    except Exception:
        return 'Local user'


class KiRiOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=diff_pcb/diff_sch, %x=pdf) """
            self.color_theme = '_builtin_classic'
            """ *Selects the color theme. Only applies to KiCad 6.
                To use the KiCad 6 default colors select `_builtin_default`.
                Usually user colors are stored as `user`, but you can give it another name """
            self.keep_generated = False
            """ *Avoid PCB and SCH images regeneration. Useful for incremental usage """
        super().__init__()
        self._expand_id = 'diff'
        self._expand_ext = 'pdf'

    def get_targets(self, out_dir):
        # TODO: Implement
        return [self._parent.expand_filename(out_dir, self.output)]

    def add_to_cache(self, name, hash):
        cmd = [self.command, '--no_reader', '--only_cache', '--old_file_hash', hash[:7], '--cache_dir', self.cache_dir,
               '--kiri_mode', '--all_pages']
        if self.incl_file:
            cmd.extend(['--layers', self.incl_file])
        if GS.debug_enabled:
            cmd.insert(1, '-'+'v'*GS.debug_level)
        cmd.extend([name, name])
        self.name_used_for_cache = name
        run_command(cmd)

    def run_git(self, cmd, cwd=None, just_raise=False):
        if cwd is None:
            cwd = self.repo_dir
        return run_command([self.git_command]+cmd, change_to=cwd, just_raise=just_raise)

    def git_dirty(self, file):
        return self.run_git(['status', '--porcelain', '-uno', file])

    def remove_git_worktree(self, name):
        logger.debug('Removing temporal checkout at '+name)
        self.run_git(['worktree', 'remove', '--force', name])

    def create_layers_incl(self, layers):
        self.incl_file = None
        if not isinstance(layers, type):
            layers = Layer.solve(layers)
            # TODO no list (ALL)
            self._solved_layers = layers
            logger.debug('Including layers:')
            with NamedTemporaryFile(mode='w', suffix='.lst', delete=False) as f:
                self.incl_file = f.name
                for la in layers:
                    logger.debug('- {} ({})'.format(la.layer, la.id))
                    f.write(str(la.id)+'\n')

    def do_cache(self, name, tmp_wd, hash):
        name_copy = self.run_git(['ls-files', '--full-name', name])
        name_copy = os.path.join(tmp_wd, name_copy)
        logger.debug('- Using temporal copy: '+name_copy)
        self.add_to_cache(name_copy, hash)
        return name_copy

    def save_pcb_layers(self, hash=None):
        subdir = os.path.join(hash[:7], '_KIRI_') if hash is not None else ''
        with open(os.path.join(self.cache_dir, subdir, 'pcb_layers'), 'wt') as f:
            for la in self._solved_layers:
                f.write(str(la.id)+'|'+la.layer+'\n')

    def solve_layer_colors(self):
        # Color theme
        self._color_theme = load_color_theme(self.color_theme)
        if self._color_theme is None:
            raise KiPlotConfigurationError("Unable to load `{}` color theme".format(self.color_theme))
        # Assign a color if none was defined
        layer_id2color = self._color_theme.layer_id2color
        for la in self._solved_layers:
            if la._id in layer_id2color:
                la.color = layer_id2color[la._id]
            else:
                la.color = "#000000"

    def create_layers(self, f):
        template = self.load_html_template('layers', 11)
        for i, la in enumerate(self._solved_layers):
            # TODO: Configure checked?
            checked = 'checked="checked"' if i == 0 else ''
            f.write(template.format(i=i+1, layer_id_padding='%02d' % (i+1), layer_name=la.suffix,
                                    layer_id=la.id, layer_color=la.color, checked=checked))

    def save_sch_sheet(self, hash, name_sch):
        # Load the schematic. Really worth?
        sch = load_any_sch(name_sch, GS.sch_basename)
        with open(os.path.join(self.cache_dir, hash[:7], '_KIRI_', 'sch_sheets'), 'wt') as f:
            base_dir = os.path.dirname(name_sch)
            for s in sch.all_sheets:
                fname = s.fname
                no_ext = os.path.splitext(os.path.basename(fname))[0]
                rel_name = os.path.relpath(fname, base_dir)
                if s.sheet_path_h == '/':
                    instance_name = sheet_path = GS.sch_basename
                else:
                    instance_name = os.path.basename(s.sheet_path_h)
                    sheet_path = s.sheet_path_h.replace('/', '-')
                    sheet_path = GS.sch_basename+'-'+sheet_path[1:]
                f.write(f'{no_ext}|{rel_name}||{instance_name}|{sheet_path}\n')

    def create_pages(self, f):
        template = self.load_html_template('pages', 11)
        for i, s in enumerate(sorted(GS.sch.all_sheets, key=lambda s: s.sheet_path_h)):
            fname = s.fname
            checked = 'checked="checked"' if i == 0 else ''
            base_name = os.path.basename(fname)
            rel_name = os.path.relpath(fname, GS.sch_dir)
            if s.sheet_path_h == '/':
                instance_name = sheet_path = GS.sch_basename
            else:
                instance_name = os.path.basename(s.sheet_path_h)
                sheet_path = s.sheet_path_h.replace('/', '-')
                sheet_path = GS.sch_basename+'-'+sheet_path[1:]
            f.write(template.format(i=i+1, page_name=instance_name, page_filename_path=rel_name,
                                    page_filename=base_name, checked=checked))

    def load_html_template(self, type, tabs):
        """ Load a template used to generate an HTML section.
            Outside of the code for easier modification/customization. """
        with open(os.path.join(GS.get_resource_path('kiri'), f'{type}_template.html'), 'rt') as f:
            template = f.read()
        template = template.replace('${', '{')
        template = template.replace('$(printf "%02d" {i})', '{i02}')
        template = template.replace('{class}', '{cls}')
        template = template.replace('\t\t', '\t'*tabs)
        return template

    def create_index(self, commits):
        # Get the KiRi template
        with open(os.path.join(GS.get_resource_path('kiri'), 'index.html'), 'rt') as f:
            template = f.read()
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        # Replacement keys
        rep = {}
        rep['PROJECT_TITLE'] = GS.pro_basename or GS.sch_basename or GS.pcb_basename or 'unknown'
        rep['SCH_TITLE'] = GS.sch_title or 'No title'
        rep['SCH_REVISION'] = GS.sch_rev or ''
        rep['SCH_DATE'] = GS.sch_date or today
        rep['PCB_TITLE'] = GS.pcb_title or 'No title'
        rep['PCB_REVISION'] = GS.pcb_rev or ''
        rep['PCB_DATE'] = GS.pcb_date or today
        # Fill the template
        with open(os.path.join(self.cache_dir, 'web', 'index.html'), 'wt') as f:
            for ln in iter(template.splitlines()):
                for k, v in rep.items():
                    ln = ln.replace(f'[{k}]', v)
                f.write(ln+'\n')
                if ln.endswith('<!-- FILL_COMMITS_HERE -->'):
                    self.create_commits(f, commits)
                elif ln.endswith('<!-- FILL_PAGES_HERE -->'):
                    self.create_pages(f)
                elif ln.endswith('<!-- FILL_LAYERS_HERE -->'):
                    self.create_layers(f)

    def create_commits(self, f, commits):
        template = self.load_html_template('commits', 8)
        for i, c in enumerate(commits):
            hash = c[0][:7]
            dt = c[1].split()[0]
            author = c[2]+' '
            desc = c[3]
            tooltip = TOOLTIP_HTML.format(hash=hash, dt=dt, author=author, desc=desc)
            cls = 'text-warning' if hash == HASH_LOCAL else 'text-info'
            icon_pcb = PCB_IMG if c[0] in self.commits_with_changed_pcb else EMPTY_IMG
            icon_sch = SCH_IMG if c[0] in self.commits_with_changed_sch else EMPTY_IMG
            # TODO What's this? if we only track changes in PCB/Sch this should be empty
            icon_txt = TXT_IMG
            f.write(template.format(i=i+1, hash=hash, tooltip=tooltip, text=c[3], cls=cls, i02='%02d' % (i+1),
                    date=dt, user=author, pcb_icon=icon_pcb, sch_icon=icon_sch, txt_icon=icon_txt, hash_label=hash))

    def get_modified_status(self, pcb_file, sch_files):
        res = self.run_git(['log', '--pretty=format:%H', '--', pcb_file])
        self.commits_with_changed_pcb = set(res.split())
        res = self.run_git(['log', '--pretty=format:%H', '--'] + sch_files)
        self.commits_with_changed_sch = set(res.split())
        if GS.debug_level > 1:
            logger.debug(f'Commits with changes in the PCB: {self.commits_with_changed_pcb}')
            logger.debug(f'Commits with changes in the Schematics: {self.commits_with_changed_sch}')

    def create_kiri_files(self):
        src_dir = GS.get_resource_path('kiri')
        copy2(os.path.join(src_dir, 'redirect.html'), os.path.join(self.cache_dir, 'index.html'))
        copy2(os.path.join(src_dir, 'kiri-server'), os.path.join(self.cache_dir, 'kiri-server'))
        web_dir = os.path.join(self.cache_dir, 'web')
        os.makedirs(web_dir, exist_ok=True)
        copy2(os.path.join(src_dir, 'blank.svg'), os.path.join(web_dir, 'blank.svg'))
        copy2(os.path.join(src_dir, 'favicon.ico'), os.path.join(web_dir, 'favicon.ico'))
        copy2(os.path.join(src_dir, 'kiri.css'), os.path.join(web_dir, 'kiri.css'))
        copy2(os.path.join(src_dir, 'kiri.js'), os.path.join(web_dir, 'kiri.js'))

    def run(self, name):
        self.cache_dir = self._parent.output_dir
        self.command = self.ensure_tool('KiDiff')
        self.git_command = self.ensure_tool('Git')
        # Get a list of files for the project
        GS.check_sch()
        sch_files = GS.sch.get_files()
        self.repo_dir = GS.sch_dir
        GS.check_pcb()
        # Get a list of hashes where we have changes
        # TODO implement a limit -n X
        res = self.run_git(['log', "--date=format:%Y-%m-%d %H:%M:%S", '--pretty=format:%H | %ad | %an | %s', '--',
                            GS.pcb_file] + sch_files)
        hashes = [r.split(' | ') for r in res.split('\n')]
        self.create_layers_incl(self.layers)
        self.solve_layer_colors()
        # Get more information about what is changed
        self.get_modified_status(GS.pcb_file, sch_files)
        # TODO ensure we have at least 2
        try:
            git_tmp_wd = None
            try:
                for h in hashes:
                    hash = h[0]
                    if self.keep_generated and os.path.isdir(os.path.join(self.cache_dir, hash[:7])):
                        logger.debug(f'- Images for {hash} already generated')
                        continue
                    git_tmp_wd = mkdtemp()
                    logger.debug('Checking out '+hash+' to '+git_tmp_wd)
                    self.run_git(['worktree', 'add', git_tmp_wd, hash])
                    self.run_git(['submodule', 'update', '--init', '--recursive'], cwd=git_tmp_wd)
                    # Generate SVGs for the schematic
                    name_sch = self.do_cache(GS.sch_file, git_tmp_wd, hash)
                    # Generate SVGs for the PCB
                    self.do_cache(GS.pcb_file, git_tmp_wd, hash)
                    # List of layers
                    self.save_pcb_layers(hash)
                    # Schematic hierarchy
                    self.save_sch_sheet(hash, name_sch)
                    self.remove_git_worktree(git_tmp_wd)
                    git_tmp_wd = None
            finally:
                if git_tmp_wd:
                    self.remove_git_worktree(git_tmp_wd)
            # Do we have modifications?
            sch_dirty = self.git_dirty(GS.sch_file)
            pcb_dirty = self.git_dirty(GS.pcb_file)
            if sch_dirty or pcb_dirty:
                # Include the current files
                name_sch = self.do_cache(GS.sch_file, GS.sch_dir, HASH_LOCAL)
                self.save_sch_sheet(HASH_LOCAL, name_sch)
                self.do_cache(GS.pcb_file, GS.pcb_dir, HASH_LOCAL)
                self.save_pcb_layers(HASH_LOCAL)
                hashes.insert(0, (HASH_LOCAL, datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'), get_cur_user(),
                              'Local changes not committed'))
                if pcb_dirty:
                    self.commits_with_changed_pcb.add(HASH_LOCAL)
                if sch_dirty:
                    self.commits_with_changed_sch.add(HASH_LOCAL)
        finally:
            if self.incl_file:
                os.remove(self.incl_file)
        self.create_kiri_files()
        self.create_index(hashes)


@output_class
class KiRi(BaseOutput):  # noqa: F821
    """ KiRi
        Generates a PDF with the differences between two PCBs or schematics.
        Recursive git submodules aren't supported (submodules inside submodules) """
    def __init__(self):
        super().__init__()
        self._category = ['PCB/docs', 'Schematic/docs']
        self._both_related = True
        with document:
            self.options = KiRiOptions
            """ *[dict] Options for the `diff` output """
            self.layers = Layer
            """ *[list(dict)|list(string)|string] [all,selected,copper,technical,user]
                List of PCB layers to use. When empty all available layers are used.
                Note that if you want to support adding/removing layers you should specify a list here """

    @staticmethod
    def layer2dict(la):
        return {'layer': la.layer, 'suffix': la.suffix, 'description': la.description}

    @staticmethod
    def has_repo(git_command, file):
        try:
            run_command([git_command, 'ls-files', '--error-unmatch', file], change_to=os.path.dirname(file), just_raise=True)
        except CalledProcessError:
            logger.debug("File `{}` not inside a repo".format(file))
            return False
        return True

    @staticmethod
    def get_conf_examples(name, layers):
        outs = []
        git_command = GS.check_tool(name, 'Git')
        # TODO: Implement
        if (GS.pcb_file and GS.sch_file and KiRi.has_repo(git_command, GS.pcb_file) and
           KiRi.has_repo(git_command, GS.sch_file)):
            gb = {}
            gb['name'] = 'basic_{}'.format(name)
            gb['comment'] = 'Interactive diff between commits'
            gb['type'] = name
            gb['dir'] = 'diff'
            gb['layers'] = [KiRi.layer2dict(la) for la in layers]
            outs.append(gb)
        return outs

    def run(self, name):
        self.options.layers = self.layers
        super().run(name)
