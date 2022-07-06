"""
Tests for Dependencies Downloader

For debug information use:
pytest-3 --log-cli-level debug
"""
import os
import coverage
import yaml
from importlib import reload
from . import context
from kibot.mcpyrate import activate  # noqa: F401
import kibot.dep_downloader as downloader
import kibot.out_compress as compress

cov = coverage.Coverage()
bin_dir = os.path.join('.local', 'share', 'kibot', 'bin')
DEPS = {'Dependencies': [{'from': 'RAR', 'role': 'mandatory'}]}


def test_dep_rar(test_dir, caplog, monkeypatch):
    """ Check missing rar_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    with monkeypatch.context() as m:
        # Force the downloader to use the output dir
        home = os.path.abspath(ctx.output_dir)
        m.setenv("HOME", home)
        # Refresh the module with actual dependencies
        mod = reload(downloader)
        mod.register_deps('test', yaml.safe_load(compress.__doc__))
        # Get the RAR dependency
        dep = mod.used_deps['test:rar']
        # Download it
        cov.load()
        cov.start()
        res = mod.rar_downloader(dep, 'Linux', 'x86_64')
        cov.stop()
        cov.save()
        # We should get the following name:
        assert res == os.path.join(home, bin_dir, 'rar')
        # We executed the file
