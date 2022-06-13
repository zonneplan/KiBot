# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2022 Albin Dennevi (create_pdf_from_pages)
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Base idea: https://gitlab.com/dennevi/Board2Pdf/ (Released as Public Domain)
from . import PyPDF2


def create_pdf_from_pages(input_files, output_fn):
    output = PyPDF2.PdfFileWriter()
    # Collect all pages
    open_files = []
    for filename in input_files:
        file = open(filename, 'rb')
        open_files.append(file)
        pdf_reader = PyPDF2.PdfFileReader(file)
        page_obj = pdf_reader.getPage(0)
        page_obj.compressContentStreams()
        output.addPage(page_obj)
    # Write all pages to a file
    with open(output_fn, 'wb') as pdf_output:
        output.write(pdf_output)
    # Close the files
    for f in open_files:
        f.close()
