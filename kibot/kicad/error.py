# -*- coding: utf-8 -*-
# Copyright (c) 2021-2023 Salvador E. Tropea
# Copyright (c) 2021-2023 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)

class SchError(Exception):
    pass


class SchFileError(SchError):
    def __init__(self, msg, code, reader):
        super().__init__()
        self.line = reader.line
        self.file = reader.file
        self.msg = msg
        self.code = code


class SchLibError(SchFileError):
    def __init__(self, msg, code, reader):
        super().__init__(msg, code, reader)
