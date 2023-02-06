# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Salvador E. Tropea
# Copyright (c) 2022-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import fnmatch
import glob
import os
import re
from shutil import copy2
from sys import exit
from .error import KiPlotConfigurationError
from .gs import GS
from .kiplot import config_output, get_output_dir, run_output
from .kicad.config import KiConf
from .misc import WRONG_ARGUMENTS, INTERNAL_ERROR, W_COPYOVER
from .optionable import Optionable
from .out_base_3d import Base3DOptions
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


def may_be_rel(file):
    rel_file = os.path.relpath(file)
    if len(rel_file) < len(file):
        return rel_file
    return file


class FilesList(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.source = '*'
            """ *File names to add, wildcards allowed. Use ** for recursive match.
                By default this pattern is applied to the current working dir.
                See the `from_outdir` option """
            self.source_type = 'files'
            """ *[files,out_files,output,3d_models] How to interpret `source`.
                `files`: is a pattern for files relative to the working directory.
                `out_files`: is a pattern for files relative to output dir specified
                with `-d` command line option.
                `output`: is the name of an `output`.
                `3d_models`: is a pattern to match the name of the 3D models extracted
                from the PCB. """
            self.filter = '.*'
            """ A regular expression that source files must match """
            self.dest = ''
            """ Destination directory inside the output dir, empty means the same of the file
                relative to the source directory.
                For the `3d_models` type you can use DIR+ to create subdirs under DIR """
            self.save_pcb = False
            """ Only usable for the `3d_models` mode.
                Save a PCB copy modified to use the copied 3D models """

    def apply_rename(self, fname):
        is_abs = os.path.isabs(fname)
        append_mode = self.dest and self.dest[-1] == '+'
        if self.dest and not append_mode:
            # A destination specified by the user
            dest = os.path.basename(fname)
        elif is_abs:
            for d in self.rel_dirs:
                if d is not None and fname.startswith(d):
                    dest = os.path.relpath(fname, d)
                    break
            else:
                dest = os.path.basename(fname)
        else:
            dest = os.path.relpath(fname, os.getcwd())
        return '${KIPRJMOD}/'+os.path.join(self.output_dir, dest)


class Copy_FilesOptions(Base3DOptions):
    def __init__(self):
        with document:
            self.files = FilesList
            """ *[list(dict)] Which files will be included """
            self.follow_links = True
            """ Store the file pointed by symlinks, not the symlink """
            self.link_no_copy = False
            """ Create symlinks instead of copying files """
        super().__init__()
        self._expand_id = 'copy'
        self._expand_ext = 'files'

    def config(self, parent):
        super().config(parent)
        if isinstance(self.files, type):
            raise KiPlotConfigurationError('No files provided')

    def get_from_output(self, f, no_out_run):
        from_output = f.source
        logger.debugl(2, '- From output `{}`'.format(from_output))
        out = RegOutput.get_output(from_output)
        if out is not None:
            config_output(out)
            out_dir = get_output_dir(out.dir, out, dry=True)
            files_list = out.get_targets(out_dir)
            logger.debugl(2, '- List of files: {}'.format(files_list))
        else:
            logger.error('Unknown output `{}` selected in {}'.format(from_output, self._parent))
            exit(WRONG_ARGUMENTS)
        # Check if we must run the output to create the files
        if not no_out_run:
            for file in files_list:
                if not os.path.isfile(file):
                    # The target doesn't exist
                    if not out._done:
                        # The output wasn't created in this run, try running it
                        run_output(out)
                    if not os.path.isfile(file):
                        # Still missing, something is wrong
                        logger.error('Unable to generate `{}` from {}'.format(file, out))
                        exit(INTERNAL_ERROR)
        return files_list

    def get_3d_models(self, f):
        """ Look for the 3D models and make a list, optionally download them """
        GS.check_pcb()
        dest_dir = f.dest
        if dest_dir and dest_dir[-1] == '+':
            dest_dir = dest_dir[:-1]
        f.output_dir = dest_dir
        # Apply any variant
        self.filter_pcb_components(do_3D=True, do_2D=True)
        # Download missing models and rename all collect 3D models (renamed)
        f.rel_dirs = self.rel_dirs
        files_list = self.download_models(rename_filter=f.source, rename_function=FilesList.apply_rename, rename_data=f)
        if f.save_pcb:
            fname = os.path.join(self.output_dir, os.path.basename(GS.pcb_file))
            logger.debug('Saving the PCB to '+fname)
            GS.board.Save(fname)
            GS.copy_project(fname)
        if not self._comps:
            # We must undo the download/rename
            self.undo_3d_models_rename(GS.board)
        else:
            self.unfilter_pcb_components(do_3D=True, do_2D=True)
        # Also include the step/wrl counterpart
        new_list = []
        for fn in files_list:
            if fn.endswith('.wrl'):
                fn = fn[:-4]+'.step'
                if os.path.isfile(fn):
                    new_list.append(fn)
            elif fn.endswith('.step'):
                fn = f[:-5]+'.wrl'
                if os.path.isfile(fn):
                    new_list.append(fn)
        return files_list+fnmatch.filter(new_list, f.source)

    def get_files(self, no_out_run=False):
        files = []
        src_dir_cwd = os.getcwd()
        src_dir_outdir = self.expand_filename_sch(GS.out_dir)
        self.rel_dirs = []
        if KiConf.models_3d_dir:
            self.rel_dirs.append(os.path.normpath(os.path.join(GS.pcb_dir, KiConf.models_3d_dir)))
        if KiConf.party_3rd_dir:
            self.rel_dirs.append(os.path.normpath(os.path.join(GS.pcb_dir, KiConf.party_3rd_dir)))
        self.rel_dirs.append(GS.pcb_dir)
        for f in self.files:
            from_outdir = False
            if f.source_type == 'out_files' or f.source_type == 'output':
                from_outdir = True
            src_dir = src_dir_outdir if from_outdir else src_dir_cwd
            mode_3d = f.source_type == '3d_models'
            mode_3d_append = mode_3d and f.dest and f.dest[-1] == '+'
            # Get the list of candidates
            files_list = None
            if f.source_type == 'output':
                files_list = self.get_from_output(f, no_out_run)
            elif mode_3d:
                files_list = self.get_3d_models(f)
            else:  # files and out_files
                source = f.expand_filename_both(f.source, make_safe=False)
                files_list = glob.iglob(os.path.join(src_dir, source), recursive=True)
                if GS.debug_level > 1:
                    files_list = list(files_list)
                    logger.debug('- Pattern {} list of files: {}'.format(source, files_list))
            # Filter and adapt them
            for fname in filter(re.compile(f.filter).match, files_list):
                fname_real = os.path.realpath(fname) if self.follow_links else os.path.abspath(fname)
                # Compute the destination directory
                dest = fname
                is_abs = os.path.isabs(fname)
                if f.dest and not mode_3d_append:
                    # A destination specified by the user
                    dest = os.path.join(f.dest, os.path.basename(fname))
                elif mode_3d and is_abs:
                    for d in self.rel_dirs:
                        if d is not None and fname.startswith(d):
                            dest = os.path.relpath(dest, d)
                            break
                    else:
                        dest = os.path.basename(fname)
                    if mode_3d_append:
                        dest = os.path.join(f.dest[:-1], dest)
                else:
                    dest = os.path.relpath(dest, src_dir)
                files.append((fname_real, dest))
        return files

    def get_targets(self, out_dir):
        self.output_dir = out_dir
        files = self.get_files(no_out_run=True)
        return sorted([os.path.join(out_dir, v) for _, v in files])

    def get_dependencies(self):
        files = self.get_files(no_out_run=True)
        return sorted([v for v, _ in files])

    def run(self, output):
        super().run(output)
        # Output file name
        logger.debug('Collecting files')
        # Collect the files
        files = self.get_files()
        logger.debug('Copying files')
        output += os.path.sep
        copied = {}
        for (src, dst) in files:
            dest = os.path.join(output, dst)
            dest_dir = os.path.dirname(dest)
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir)
            logger.debug('- {} -> {}'.format(src, dest))
            if dest in copied:
                logger.warning(W_COPYOVER+'`{}` and `{}` both are copied to `{}`'.
                               format(may_be_rel(src), may_be_rel(copied[dest]), may_be_rel(dest)))
            try:
                if os.path.samefile(src, dest):
                    raise KiPlotConfigurationError('Trying to copy {} over itself {}'.format(src, dest))
            except FileNotFoundError:
                pass
            if os.path.isfile(dest) or os.path.islink(dest):
                os.remove(dest)
            if self.link_no_copy:
                os.symlink(os.path.relpath(src, os.path.dirname(dest)), dest)
            else:
                copy2(src, dest)
            copied[dest] = src
        # Remove the downloaded 3D models
        self.remove_temporals()


@output_class
class Copy_Files(BaseOutput):  # noqa: F821
    """ Files copier
        Used to copy files to the output directory.
        Useful when an external tool is used to compress the output directory.
        Note that you can use the `compress` output to create archives """
    def __init__(self):
        super().__init__()
        # Make it low priority so it gets created after all the other outputs
        self.priority = 11
        with document:
            self.options = Copy_FilesOptions
            """ *[dict] Options for the `copy_files` output """
        self._none_related = True
        # The help is inherited and already mentions the default priority
        self.fix_priority_help()

    def get_dependencies(self):
        return self.options.get_dependencies()

    def run(self, output_dir):
        # No output member, just a dir
        self.options.output_dir = output_dir
        self.options.run(output_dir)
