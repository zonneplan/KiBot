#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
This will generate the .pot and .mo files for the application domain and
languages defined below.

The .po and .mo files are placed as per convention in

"appfolder/locale/lang/LC_MESSAGES"

The .pot file is placed in the locale folder.

This script or something similar should be added to your build process.

The actual translation work is normally done using a tool like poEdit or
similar, it allows you to generate a particular language catalog from the .pot
file or to use the .pot to merge new translations into an existing language
catalog.

"""

import os
import sys

appFolder = os.getcwd()
sys.path.insert(0, os.path.dirname(appFolder))
script_dir = os.path.dirname(os.path.abspath(os.path.realpath(appFolder)))
# Pretend we are part of a module
# Avoids: ImportError: attempted relative import with no known parent package
__package__ = os.path.basename(script_dir)
__import__(__package__)
from .GUI.gui_config import sup_lang, lang_domain

# we remove English as source code strings are in English
supportedLang = []
for lang in sup_lang:
    if lang != u"en":
        supportedLang.append(lang)

import subprocess


# setup some stuff to get at Python I18N tools/utilities

pyExe = sys.executable
pyFolder = os.path.split(pyExe)[0]
# pyToolsFolder = os.path.join(pyFolder, 'Tools')
# pyI18nFolder = os.path.join(pyToolsFolder, 'i18n')
pyI18nFolder = os.path.dirname(__file__)
pyGettext = os.path.join(pyI18nFolder, 'pygettext.py')
pyMsgfmt = os.path.join(pyI18nFolder, 'msgfmt.py')
outFolder = os.path.join(appFolder, 'locale')

# build command for pygettext
cmd = [pyExe, pyGettext, '-a', '-d', lang_domain, '-o', lang_domain+'.pot', '-p', outFolder, appFolder]

print("Generating the .pot file")
print("cmd: %s" % cmd)
rCode = subprocess.call(cmd)
print("return code: %s\n\n" % rCode)

potFile = os.path.join(outFolder, lang_domain+'.pot')

for tLang in supportedLang:
    langDir = os.path.join(appFolder, ('locale/%s/LC_MESSAGES' % tLang))
    poFile = os.path.join(langDir, lang_domain + '.po')
    # Merge the files
    cmd = ['msgmerge', '-U', poFile, potFile]
    print("Updating the .po file")
    print("cmd: %s" % cmd)
    rCode = subprocess.call(cmd)
    print("return code: %s\n\n" % rCode)

    # build command for msgfmt
    cmd = [pyExe, pyMsgfmt, poFile]

    print("Generating the .mo file")
    print("cmd: %s" % cmd)
    rCode = subprocess.call(cmd)
    print("return code: %s\n\n" % rCode)
