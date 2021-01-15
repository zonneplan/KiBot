# -*- coding: utf-8 -*-
# Copyright (c) 2021 Salvador E. Tropea
# Copyright (c) 2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import re
import os
import glob
from sys import exit
from subprocess import check_output, STDOUT, CalledProcessError
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED, ZIP_BZIP2, ZIP_LZMA
from tarfile import open as tar_open
from collections import OrderedDict
from .gs import GS
from .misc import MISSING_TOOL, WRONG_INSTALL, W_EMPTYZIP
from .optionable import Optionable, BaseOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class FilesList(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.source = '*'
            """ File names to add, wildcards allowed. Use ** for recursive match.
                Note this pattern is applied to the output dir specified with -d comman line option """
            self.filter = '.*'
            """ A regular expression that source files must match """
            self.dest = ''
            """ Destination directory inside the archive, empty means the same of the file """


class CompressOptions(BaseOptions):
    ZIP_ALGORITHMS = {'auto': ZIP_DEFLATED,
                      'stored': ZIP_STORED,
                      'deflated': ZIP_DEFLATED,
                      'bzip2': ZIP_BZIP2,
                      'lzma': ZIP_LZMA}
    TAR_MODE = {'auto': 'bz2',
                'stored': '',
                'deflated': 'gz',
                'bzip2': 'bz2',
                'lzma': 'xz'}

    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ Name for the generated archive (%i=name of the output %x=according to format) """
            self.format = 'ZIP'
            """ [ZIP,TAR,RAR] Output file format """
            self.compression = 'auto'
            """ [auto,stored,deflated,bzip2,lzma] Compression algorithm. Use auto to let KiBot select a suitable one """
            self.files = FilesList
            """ [list(dict)] Which files will be included """
        super().__init__()

    def config(self):
        super().config()
        if isinstance(self.files, type):
            self.files = []
            logger.warning(W_EMPTYZIP+' No files provided, creating an empty archive')

    def create_zip(self, output, files):
        with ZipFile(output, 'w', compression=self.ZIP_ALGORITHMS[self.compression], compresslevel=9) as zip:
            for fname, dest in files.items():
                logger.debug('Adding '+fname+' as '+dest)
                zip.write(fname, dest)

    def create_tar(self, output, files):
        with tar_open(output, 'w:'+self.TAR_MODE[self.compression]) as tar:
            for fname, dest in files.items():
                logger.debug('Adding '+fname+' as '+dest)
                tar.add(fname, dest)

    def create_rar(self, output, files):
        if os.path.isfile(output):
            os.remove(output)
        for fname, dest in files.items():
            logger.debug('Adding '+fname+' as '+dest)
            cmd = ['rar', 'a', '-m5', '-ep', '-ap'+os.path.dirname(dest), output, fname]
            try:
                check_output(cmd, stderr=STDOUT)
            except FileNotFoundError:
                logger.error('Missing `rar` command, install it')
                exit(MISSING_TOOL)
            except CalledProcessError as e:  # pragma: no cover
                logger.error('Failed to invoke rar command, error {}'.format(e.returncode))
                if e.output:
                    logger.debug('Output from command: '+e.output.decode())
                exit(WRONG_INSTALL)

    def solve_extension(self):
        if self.format == 'ZIP':
            return 'zip'
        if self.format == 'RAR':
            return 'rar'
        # TAR
        ext = 'tar'
        sub_ext = self.TAR_MODE[self.compression]
        if sub_ext:
            ext += '.'+sub_ext
        return ext

    def run(self, output_dir, board):
        # Output file name
        logger.debug('output_dir '+output_dir)
        logger.debug('GS.out_dir '+GS.out_dir)
        output = self.expand_filename(output_dir, self.output, GS.current_output, self.solve_extension())
        logger.debug('Collecting files')
        output_real = os.path.realpath(output)
        # Collect the files
        files = OrderedDict()
        for f in self.files:
            for fname in filter(re.compile(f.filter).match, glob.iglob(os.path.join(GS.out_dir, f.source), recursive=True)):
                fname_real = os.path.realpath(fname)
                # Avoid including the output
                if fname_real == output_real:
                    continue
                # Compute the destination directory inside the archive
                dest = fname
                if f.dest:
                    dest = os.path.join(f.dest, os.path.basename(fname))
                else:
                    dest = os.path.relpath(dest, GS.out_dir)
                files[fname_real] = dest
        logger.debug('Generating `{}` archive'.format(output))
        if self.format == 'ZIP':
            self.create_zip(output, files)
        elif self.format == 'TAR':
            self.create_tar(output, files)
        elif self.format == 'RAR':
            self.create_rar(output, files)


@output_class
class Compress(BaseOutput):  # noqa: F821
    """ Archiver (files compressor)
        Generates a compressed file containing output files.
        This is used to generate groups of files in compressed file format. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = CompressOptions
            """ [dict] Options for the `compress` output """
