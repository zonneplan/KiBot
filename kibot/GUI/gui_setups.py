# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnologïa Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
#
# Memorizes setups used

from dataclasses import dataclass, asdict, make_dataclass
import os
import os.path as op
import yaml
from .. import log
CONFIG = '~/.config/kibot/gui.yaml'
cfg_file = op.expanduser(CONFIG)
MAX_SETUPS = 20
LEN_CWD = 40
logger = log.get_logger()
setups = []


@dataclass()
class Setup(object):
    config: str
    cwd: str
    dest: str
    pcb: str
    schematic: str

    def __eq__(self, other):
        # Why the default is different?!
        return (self.config == other.config and self.cwd == other.cwd and self.dest == other.dest and
                self.pcb == other.pcb and self.schematic == other.schematic)

    def __str__(self):
        cwd = self.cwd
        if len(cwd) > LEN_CWD:
            cwd = '...'+self.cwd[-LEN_CWD:]
        return op.basename(op.splitext(self.schematic)[0])+' | '+op.basename(self.config)+' | '+cwd


def init():
    if op.isfile(cfg_file):
        try:
            with open(cfg_file, 'rt') as f:
                data = yaml.safe_load(f)
            for s in data.get('setups', []):
                new_setup = make_dataclass("Setup", ((k, type(v)) for k, v in s.items()))(**s)
                setups.append(new_setup)
        except Exception as e:
            logger.error(f'Error loading GUI state: {e}')


def add_setup(new_setup):
    global setups
    try:
        setups.remove(new_setup)
    except ValueError:
        pass
    setups.insert(0, new_setup)
    if len(setups) > MAX_SETUPS:
        setups = setups[:MAX_SETUPS]


def get_valid_setups(cur_setup):
    res = []
    for s in setups:
        if s == cur_setup:
            continue
        cwd = s.cwd
        sch = op.join(cwd, s.schematic)
        pcb = op.join(cwd, s.pcb)
        cfg = op.join(cwd, s.config)
        dest = op.join(cwd, s.dest)
        # Let the GUI verify them, can provide more info to the user
        # if op.isfile(sch) and op.isfile(pcb) and op.isfile(cfg) and op.isdir(cwd) and op.isdir(dest):
        res.append(Setup(cfg, cwd, dest, pcb, sch))
    return res


def save_setups():
    if not setups:
        return
    try:
        os.makedirs(op.dirname(cfg_file), exist_ok=True)
        with open(cfg_file, 'wt') as f:
            f.write(yaml.dump({'setups': [asdict(s) for s in setups]}))
    except Exception as e:
        logger.error(f'Error saving GUI state: {e}')
