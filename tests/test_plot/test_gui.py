"""
Tests the GUI.

For debug information use:
pytest-3 --log-cli-level debug
"""
from contextlib import contextmanager
import csv
import logging
import os
import signal
from subprocess import Popen, TimeoutExpired
import sys
from xvfbwrapper import Xvfb
from . import context
CSVDIR = "tests/GUI/CSV/"
MAIN_OUPUTS_PAGE = 1


class PopenContext(Popen):

    def __exit__(self, type, value, traceback):
        logging.debug("Closing pipe with %d", self.pid)
        # Note: currently we don't communicate with the child so these cases are never used.
        # I keep them in case they are needed, but excluded from the coverage.
        # Also note that closing stdin needs extra handling, implemented in the parent class
        # but not here.
        # This can generate a deadlock
        # if self.stdout:
        #     self.stdout.close()  # pragma: no cover
        if self.stderr:
            self.stderr.close()  # pragma: no cover
        if self.stdin:
            self.stdin.close()   # pragma: no cover
        if type:
            logging.debug("Terminating %d", self.pid)
            # KiCad nightly uses a shell script as intermediate to run setup the environment
            # and run the proper binary. If we simply call "terminate" we just kill the
            # shell script. So we create a group and then kill the whole group.
            try:
                os.killpg(os.getpgid(self.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            # self.terminate()
        # Wait for the process to terminate, to avoid zombies.
        try:
            # Wait for 3 seconds
            self.wait(3)
            retry = False
        except TimeoutExpired:  # pragma: no cover
            # The process still alive after 3 seconds
            retry = True
        if retry:  # pragma: no cover
            logging.debug("Killing %d", self.pid)
            # We shouldn't get here. Kill the process and wait upto 10 seconds
            os.killpg(os.getpgid(self.pid), signal.SIGKILL)
            # self.kill()
            self.wait(10)


@contextmanager
def start_record(do_record, video_dir, video_name):
    if do_record:
        video_filename = os.path.join(video_dir, video_name)
        cmd = ['recordmydesktop', '--overwrite', '--no-sound', '--no-frame', '--on-the-fly-encoding',
               '-o', video_filename]
        logging.debug('Recording session with: '+str(cmd))
        with PopenContext(cmd, start_new_session=True) as screencast_proc:
            try:
                yield
            finally:
                logging.debug('Terminating the session recorder')
                screencast_proc.terminate()
    else:
        yield


class Events(object):
    def __init__(self):
        super().__init__()
        self.e = []

    def wait(self, w):
        self.e.append(['', '_WaitDialog', w])

    def wait_splash(self):
        self.wait('splash')

    def wait_main(self):
        self.wait('main_dialog')

    def start(self):
        self.wait_splash()
        self.wait_main()

    def set_path(self, id, cfg):
        self.e.append([id, 'SetPath', cfg])

    def send_event(self, id, ev_name):
        self.e.append([id, '_SendEvent', ev_name])

    def set_cfg(self, cfg):
        self.set_path('ID_CFG_FILE', cfg)
        self.send_event('ID_CFG_FILE', 'EVT_FILEPICKER_CHANGED')

    def set_sch(self, sch):
        self.set_path('ID_SCH', sch)
        self.send_event('ID_SCH', 'EVT_FILEPICKER_CHANGED')

    def set_selection(self, id, selected):
        self.e.append([id, 'SetSelection', selected])

    def set_choice(self, id, selected):
        self.e.append([id, 'SetSelection', selected])
        self.send_event(id, 'EVT_CHOICE')

    def check_path(self, id, path):
        self.e.append([id, '_CheckPath', path])

    def sel_outputs_page(self):
        self.set_selection('ID_MAIN_NOTEBOOK', MAIN_OUPUTS_PAGE)

    def send_text(self, id, txt):
        self.e.append([id, '_SendText', txt])

    def send_key(self, id, key):
        self.e.append([id, '_SendKey', key])

    def new_output(self, name):
        self.send_event('output.add', 'EVT_BUTTON')
        self.wait('choose_an output type')
        self.send_text('ID_CHOOSE', name)
        self.send_key('ID_CHOOSE_SRCH', 'wx.WXK_RETURN')
        self.wait('output.'+name)

    def set_value(self, id, value):
        self.e.append([id, 'SetValue', value])

    def edit_dict(self, id):
        self.send_event(id, 'EVT_BUTTON')
        self.wait(id)

    def ok(self):
        self.send_event('wx.ID_OK', 'EVT_BUTTON')

    def press_button(self, name):
        self.send_event('name:'+name, 'EVT_BUTTON')

    def save(self):
        self.send_event('ID_SAVE', 'EVT_BUTTON')

    def esc(self):
        self.send_key('', 'wx.WXK_ESCAPE')

    def save_events(self, cfg):
        with open(cfg, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(self.e)


def run_test(num, test_dir, project, recipe, keep_project=False, no_board_file=False, no_yaml_file=False):
    id = "%04d" % num
    base_name = sys._getframe(1).f_code.co_name[9:]
    yaml_base = f'{id}.kibot.yaml'
    yaml_ori = os.path.abspath('tests/GUI/cfg_in/'+yaml_base)
    logging.debug(f'Using `{yaml_ori}` config name')
    assert os.path.isfile(yaml_ori)
    with open(yaml_ori) as f:
        yaml_txt = f.read()
    ctx = context.TestContext(test_dir, project, yaml_ori, test_name=sys._getframe(1).f_code.co_name)
    cfg = ctx.get_out_path('events.csv')
    recipe(ctx).save_events(cfg)
    logging.debug(f'Using `{cfg}` events')

    yaml_out = ctx.get_out_path('result.kibot.yaml')
    try:
        with Xvfb(width=1920, height=1080, colordepth=24):
            with start_record(True, ctx.output_dir, base_name):
                extra = ['--gui', '-I', cfg]
                ctx.run(extra=extra, no_board_file=no_board_file, no_yaml_file=no_yaml_file)
    finally:
        with open(yaml_ori) as f:
            yaml_res = f.read()
        with open(yaml_ori, 'w') as f:
            f.write(yaml_txt)
        with open(yaml_out, 'w') as f:
            f.write(yaml_res)
    ctx.compare_txt(text=os.path.abspath(yaml_out), reference=os.path.abspath('tests/GUI/cfg_out/'+yaml_base))
    ctx.clean_up(keep_project=keep_project)


def new_board_view_recipe(ctx):
    e = Events()
    e.start()
    e.set_cfg(ctx.yaml_file)
    e.set_sch(ctx.sch_file)
    # Check that setting the SCH is enough to also get the PCB
    e.check_path('ID_PCB', 'light_control.kicad_pcb')
    e.sel_outputs_page()
    e.new_output('boardview')
    e.set_value('output.boardview.name.string', 'test_output')
    e.ok()
    e.wait_main()
    e.save()
    e.esc()
    return e


def new_board_view_deep_recipe(ctx):
    e = Events()
    e.start()
    e.check_path('ID_CFG_FILE', 'tests/GUI/cfg_in/0002.kibot.yaml')
    e.check_path('ID_SCH', 'light_control.kicad_sch')
    e.check_path('ID_PCB', 'light_control.kicad_pcb')
    e.sel_outputs_page()
    e.new_output('boardview')
    e.set_value('output.boardview.name.string', 'test_output')
    e.edit_dict('output.boardview.options.dict')
    # Advanced options
    e.set_selection('output.boardview.options.dict.notebook', 1)
    # BVR format
    e.set_choice('output.boardview.options.dict.format.string', 1)
    e.press_button('output.boardview.options.dict.ok')
    e.wait('output.boardview')
    e.press_button('output.boardview.ok')
    e.wait_main()
    e.save()
    e.esc()
    return e


def test_gui_new_board_view_1(test_dir):
    """ We start without config.
        Force a known YAML, set an SCH, add a boardview output, name it test_output and save """
    run_test(1, test_dir, 'light_control', new_board_view_recipe, keep_project=True, no_board_file=True, no_yaml_file=True)


def test_gui_new_board_view_2(test_dir):
    """ We start with config and SCH.
        Add a boardview output, name it test_output and save """
    run_test(2, test_dir, 'light_control', new_board_view_deep_recipe, keep_project=True)
