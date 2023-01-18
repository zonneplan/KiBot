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
import pytest
import shutil
import subprocess
import sys
from . import context
from kibot.mcpyrate import activate  # noqa: F401
import kibot.dep_downloader as downloader
import kibot.out_compress as compress
import kibot.out_kibom as kibom
import kibot.log as log

cov = coverage.Coverage()
bin_dir = os.path.join('.local', 'share', 'kibot', 'bin')
bin_dir_py = os.path.join('.local', 'bin')


def try_dependency(ctx, caplog, monkeypatch, docstring, name_dep, downloader_name, b_dir, use_wrapper=False):
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
        if use_wrapper:
            dep.downloader = downloader_func
            res, version = mod.try_download_tool_binary(dep)
            if res:
                res, version = mod.check_tool_binary_local(dep)
        else:
            res, version = downloader_func(dep, 'Linux', 'x86_64')
        cov.stop()
        cov.save()
        # We should get the following name:
        logging.debug('Result: {} Version: {}'.format(res, version))
        with open(ctx.get_out_path('caplog.txt'), 'wt') as f:
            f.write(caplog.text)
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
        res, version = downloader_func(dep)
        cov.stop()
        cov.save()
        # We should get the following name:
        logging.debug('Result: {} Version: {}'.format(res, version))
        assert res is not None
        assert res.__file__ is not None


def test_dep_rar(test_dir, caplog, monkeypatch):
    """ Check the rar_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    try_dependency(ctx, caplog, monkeypatch, compress.__doc__, 'rar', 'rar', bin_dir, use_wrapper=True)


@pytest.mark.slow
def test_dep_pytool(test_dir, caplog, monkeypatch):
    """ Check the pytool_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    try_dependency(ctx, caplog, monkeypatch, kibom.__doc__, 'kibom', 'pytool', bin_dir_py)


@pytest.mark.slow
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


@pytest.mark.slow
def test_dep_gs(test_dir, caplog, monkeypatch):
    """ Check the git_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    dep = '  - from: Ghostscript\n    role: mandatory\n'
    try_dependency(ctx, caplog, monkeypatch, downloader.__doc__+dep, 'ghostscript', 'gs', bin_dir)
    os.remove(os.path.join(ctx.output_dir, bin_dir, 'gs'))


# @pytest.mark.xfail(True, reason="URL down", run=True, raises=AssertionError)
# https://imagemagick.org/archive/binaries/magick
@pytest.mark.slow
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
    # Ensure we don't have engineering-notation
    try:
        import engineering_notation
        logging.debug('Test module is already installed, using pip to uninstall ...')
        subprocess.run(['pip', 'uninstall', '-y', 'engineering-notation'])
        # Why pip does this???!!!
        dir_name = os.path.dirname(engineering_notation.__file__)
        if os.path.isdir(dir_name):
            logging.debug('Silly pip left things that will allow importing a non-existent module, removing it')
            shutil.rmtree(dir_name)
        logging.debug('Removing engineering_notation from memory')
        del sys.modules["engineering_notation"]
    except Exception as e:
        logging.error(e)
    dep = 'Dependencies:\n  - name: engineering_notation\n    role: mandatory\n    python_module: true\n'
    try_dependency_module(ctx, caplog, monkeypatch, dep, 'engineering_notation', 'check_tool_python')
