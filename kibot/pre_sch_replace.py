# -*- coding: utf-8 -*-
# Copyright (c) 2021 Salvador E. Tropea
# Copyright (c) 2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
import re
import sys
from subprocess import run, PIPE
from .gs import GS
from .error import KiPlotConfigurationError
from .optionable import Optionable
from .kiplot import load_sch
from .misc import W_EMPTREP, FAILED_EXECUTE
from .macros import macros, document, pre_class  # noqa: F401
from . import log

logger = log.get_logger()


class TagReplace(Optionable):
    """ Tags to be replaced """
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.tag = ''
            """ Name of the tag to replace. Use `version` for a tag named `@version@` """
            self.tag_delimiter = '@'
            """ Character used to indicate the beginning and the end of a tag.
                Don't change it unless you really know about KiCad's file formats """
            self.text = ''
            """ Text to insert instead of the tag """
            self.command = ''
            """ Command to execute to get the text, will be used only if `text` is empty.
                KIBOT_SCH_NAME variable is the name of the current sheet.
                KIBOT_TOP_SCH_NAME variable is the name of the top sheet """
            self.before = ''
            """ Text to add before the output of `command` """
            self.after = ''
            """ Text to add after the output of `command` """

    def config(self, parent):
        super().config(parent)
        if not self.tag:
            raise KiPlotConfigurationError("No tag to replace specified ({})".format(str(self._tree)))
        self.tag = self.tag_delimiter + re.escape(self.tag) + self.tag_delimiter


class SCH_ReplaceOptions(Optionable):
    """ A list of filter entries """
    def __init__(self):
        super().__init__()
        with document:
            self.date_command = ''
            """ Command to get the date to use in the schematic.
                git log -1 --format='%as' -- $KIBOT_SCH_NAME
                Will return the date in YYYY-MM-DD format.
                date -d @`git log -1 --format='%at' -- $KIBOT_SCH_NAME` +%Y-%m-%d_%H-%M-%S
                Will return the date in YYYY-MM-DD_HH-MM-SS format """
            self.replace_tags = TagReplace
            """ [dict|list(dict)] Tag or tags to replace """

    def config(self, parent):
        super().config(parent)
        if isinstance(self.replace_tags, type):
            self.replace_tags = []
        elif isinstance(self.replace_tags, TagReplace):
            self.replace_tags = [self.replace_tags]


@pre_class
class SCH_Replace(BasePreFlight):  # noqa: F821
    """ [dict] Replaces tags in the schematic. I.e. to insert the git hash or last revision date """
    def __init__(self, name, value):
        o = SCH_ReplaceOptions()
        o.set_tree(value)
        o.config(self)
        super().__init__(name, o)

    def get_example():
        """ Returns a YAML value for the example config """
        return ("\n    date_command: \"git log -1 --format='%as' -- $KIBOT_SCH_NAME\""
                "\n    replace_tags:"
                "\n      - tag: '@git_hash@'"
                "\n        command: 'git log -1 --format=\"%h\" $KIBOT_SCH_NAME'"
                "\n        before: 'Git hash: <'"
                "\n        after: '>'\n")

    @classmethod
    def get_doc(cls):
        return cls.__doc__, SCH_ReplaceOptions

    def replace_in_sch(self, file):
        logger.debug('Applying replacements to `{}`'.format(file))
        with open(file, 'rt') as f:
            content = f.read()
        os.environ['KIBOT_SCH_NAME'] = file
        o = self._value
        for r in o.replace_tags:
            text = r.text
            if not text:
                cmd = ['/bin/bash', '-c', r.command]
                result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                if result.returncode:
                    logger.error('Failed to execute:\n{}\nreturn code {}'.format(r.command, result.returncode))
                    sys.exit(FAILED_EXECUTE)
                if not result.stdout:
                    logger.warning(W_EMPTREP+"Empty value from `{}` skipping it".format(r.command))
                    continue
                text = result.stdout.strip()
            text = r.before + text + r.after
            logger.debug('- ' + r.tag + ' -> ' + text)
            content = re.sub(r.tag, text, content, flags=re.MULTILINE)
        os.rename(file, file + '-bak')
        with open(file, 'wt') as f:
            f.write(content)

    def apply(self):
        o = self._value
        if o.date_command:
            # Convert it into another replacement
            t = TagReplace()
            t.tag = '^Date \"(.*)\"$'
            t.command = o.date_command
            t.before = 'Date "'
            t.after = '"'
            o.replace_tags.append(t)
        load_sch()
        os.environ['KIBOT_TOP_SCH_NAME'] = GS.sch_file
        for file in GS.sch.get_files():
            self.replace_in_sch(file)
        # Force the schematic reload
        GS.sch = None
