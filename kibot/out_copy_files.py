# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from collections import OrderedDict
import glob
import os
import re
from shutil import copy2
from sys import exit
from .error import KiPlotConfigurationError
from .gs import GS
from .kiplot import config_output, get_output_dir, run_output
from .misc import WRONG_ARGUMENTS, INTERNAL_ERROR
from .optionable import Optionable, BaseOptions
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class FilesList(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.source = '*'
            """ *File names to add, wildcards allowed. Use ** for recursive match.
                By default this pattern is applied to the current working dir.
                See the `from_outdir` option """
            self.from_outdir = False
            """ Use the output dir specified with `-d` command line option, not the working dir """
            self.from_output = ''
            """ *Collect files from the selected output.
                When used the `source` option is ignored """
            self.filter = '.*'
            """ A regular expression that source files must match """
            self.dest = ''
            """ Destination directory inside the output dir, empty means the same of the file """


class Copy_FilesOptions(BaseOptions):
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
            KiPlotConfigurationError('No files provided')

    def get_files(self, no_out_run=False):
        files = OrderedDict()
        src_dir_cwd = os.getcwd()
        src_dir_outdir = self.expand_filename_sch(GS.out_dir)
        for f in self.files:
            src_dir = src_dir_outdir if f.from_outdir else src_dir_cwd
            # Get the list of candidates
            files_list = None
            if f.from_output:
                logger.debugl(2, '- From output `{}`'.format(f.from_output))
                out = RegOutput.get_output(f.from_output)
                if out is not None:
                    config_output(out)
                    out_dir = get_output_dir(out.dir, out, dry=True)
                    files_list = out.get_targets(out_dir)
                    logger.debugl(2, '- List of files: {}'.format(files_list))
                else:
                    logger.error('Unknown output `{}` selected in {}'.format(f.from_output, self._parent))
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
            else:
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
                if f.dest:
                    dest = os.path.join(f.dest, os.path.basename(fname))
                else:
                    dest = os.path.relpath(dest, src_dir)
                files[fname_real] = dest
        return files

    def get_targets(self, out_dir):
        files = self.get_files(no_out_run=True)
        return sorted([os.path.join(out_dir, v) for v in files.values()])

    def get_dependencies(self):
        files = self.get_files(no_out_run=True)
        return files.keys()

    def run(self, output):
        # Output file name
        logger.debug('Collecting files')
        # Collect the files
        files = self.get_files()
        logger.debug('Copying files')
        output += os.path.sep
        for k, v in files.items():
            src = k
            dest = os.path.join(output, v)
            dest_dir = os.path.dirname(dest)
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir)
            logger.debug('- {} -> {}'.format(src, dest))
            if os.path.isfile(dest) or os.path.islink(dest):
                os.remove(dest)
            if self.link_no_copy:
                os.symlink(os.path.relpath(src, os.path.dirname(dest)), dest)
            else:
                copy2(src, dest)


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
        self.options.run(output_dir)
