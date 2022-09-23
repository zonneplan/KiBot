# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2022 Albin Dennevi (create_pdf_from_pages)
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Base idea: https://gitlab.com/dennevi/Board2Pdf/ (Released as Public Domain)
from . import PyPDF2
from . import log

logger = log.get_logger()


def create_pdf_from_pages(input_files, output_fn, forced_width=None):
    output = PyPDF2.PdfFileWriter()
    # Collect all pages
    open_files = []
    for filename in input_files:
        file = open(filename, 'rb')
        open_files.append(file)
        pdf_reader = PyPDF2.PdfFileReader(file)
        page_obj = pdf_reader.getPage(0)
        if forced_width is not None:
            width = float(page_obj.mediaBox.getWidth())*25.4/72
            scale = round(forced_width/width, 4)
            logger.debugl(1, 'PDF scale {} ({} -> {})'.format(scale, width, forced_width))
            if abs(1.0-scale) > 0.0001:
                page_obj.scaleBy(scale)
        page_obj.compressContentStreams()
        output.addPage(page_obj)
    # Write all pages to a file
    with open(output_fn, 'wb') as pdf_output:
        output.write(pdf_output)
    # Close the files
    for f in open_files:
        f.close()
