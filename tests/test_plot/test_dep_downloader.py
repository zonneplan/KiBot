"""
Tests for Dependencies Downloader

For debug information use:
pytest-3 --log-cli-level debug
"""
import os
import coverage
import yaml
import logging
import importlib
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
        mod = importlib.reload(downloader)
        mod.register_deps('test', yaml.safe_load(docstring))
        # Get the dependency
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


def try_dependency_module(ctx, caplog, monkeypatch, docstring, name_dep, downloader_name):
    # Note: every attempt to install in a chosen dir failed, even when the module was there and in the sys.path the
    # importlib call miserably failed.
    with monkeypatch.context():
        # Refresh the module with actual dependencies
        mod = importlib.reload(downloader)
        mod.register_deps('test', yaml.safe_load(docstring))
        # Get the dependency
        dep = mod.used_deps['test:'+name_dep]
        # Download it
        cov.load()
        cov.start()
        # Python module
        downloader_func = getattr(mod, downloader_name)
        res = downloader_func(dep)
        cov.stop()
        cov.save()
        # We should get the following name:
        logging.debug('Result: {}'.format(res))
        assert res is not None
        logging.debug(res.__file__)
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


def test_dep_rsvg(test_dir, caplog, monkeypatch):
    """ Check the rsvg_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    dep = '  - from: RSVG\n    role: mandatory\n'
    try_dependency(ctx, caplog, monkeypatch, downloader.__doc__+dep, 'rsvg', 'rsvg', bin_dir)


def test_dep_git(test_dir, caplog, monkeypatch):
    """ Check the git_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    dep = '  - from: Git\n    role: mandatory\n'
    try_dependency(ctx, caplog, monkeypatch, downloader.__doc__+dep, 'git', 'git', bin_dir)


def test_dep_convert(test_dir, caplog, monkeypatch):
    """ Check the convert_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    dep = '  - from: ImageMagick\n    role: mandatory\n'
    try_dependency(ctx, caplog, monkeypatch, downloader.__doc__+dep, 'imagemagick', 'convert', bin_dir)


def test_dep_python(test_dir, caplog, monkeypatch):
    """ Check the python_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    dep = 'Dependencies:\n  - name: engineering_notation\n    role: mandatory\n    python_module: true\n'
    try_dependency_module(ctx, caplog, monkeypatch, dep, 'engineering_notation', 'check_tool_python')
