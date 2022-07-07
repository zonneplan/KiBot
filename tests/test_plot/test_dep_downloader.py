"""
Tests for Dependencies Downloader

For debug information use:
pytest-3 --log-cli-level debug
"""
import os
import coverage
import yaml
import logging
from importlib import reload
from . import context
from kibot.mcpyrate import activate  # noqa: F401
import kibot.dep_downloader as downloader
import kibot.out_compress as compress
import kibot.out_kibom as kibom
import kibot.log as log

cov = coverage.Coverage()
bin_dir = os.path.join('.local', 'share', 'kibot', 'bin')
bin_dir_py = os.path.join('.local', 'bin')
# DEPS = {'Dependencies':
#         [{'from': 'RAR', 'role': 'mandatory'},
#          {'name': 'KiBoM', 'role': 'mandatory', 'github': 'INTI-CMNB/KiBoM', 'command': 'KiBOM_CLI.py', 'version': '1.8.0'}]}


def try_dependency(ctx, caplog, monkeypatch, docstring, name_dep, downloader_name, b_dir):
    with monkeypatch.context() as m:
        # Force the downloader to use the output dir instead of HOME
        home = os.path.abspath(ctx.output_dir)
        m.setenv("HOME", home)
        m.setattr("site.USER_BASE", os.path.join(home, '.local'))
        # Refresh the module with actual dependencies
        mod = reload(downloader)
        mod.register_deps('test', yaml.safe_load(docstring))
        # Get the RAR dependency
        dep = mod.used_deps['test:'+name_dep]
        # Download it
        cov.load()
        cov.start()
        downloader_func = getattr(mod, downloader_name+'_downloader')
        res = downloader_func(dep, 'Linux', 'x86_64')
        cov.stop()
        cov.save()
        # We should get the following name:
        logging.debug('Result: {}'.format(res))
        assert res == os.path.join(home, b_dir, dep.command)
        # We executed the file


def test_dep_rar(test_dir, caplog, monkeypatch):
    """ Check the rar_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    try_dependency(ctx, caplog, monkeypatch, compress.__doc__, 'rar', 'rar', bin_dir)


def test_dep_pytool(test_dir, caplog, monkeypatch):
    """ Check the pytool_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    try_dependency(ctx, caplog, monkeypatch, kibom.__doc__, 'kibom', 'pytool', bin_dir_py)
