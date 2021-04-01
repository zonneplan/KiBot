# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import re
import os
import requests
import tempfile
from subprocess import (check_output, STDOUT, CalledProcessError)
from tempfile import NamedTemporaryFile
from shutil import rmtree
from .error import KiPlotConfigurationError
from .misc import KICAD2STEP, KICAD2STEP_ERR, W_MISS3D, W_FAILDL
from .gs import (GS)
from .out_base import VariantOptions
from .kicad.config import KiConf
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class STEPOptions(VariantOptions):
    def __init__(self):
        with document:
            self.metric_units = True
            """ Use metric units instead of inches """
            self._origin = 'grid'
            """ Determines the coordinates origin. Using grid the coordinates are the same as you have in the design sheet.
                The drill option uses the auxiliary reference defined by the user.
                You can define any other origin using the format 'X,Y', i.e. '3.2,-10' """
            self.no_virtual = False
            """ Used to exclude 3D models for components with 'virtual' attribute """
            self.min_distance = -1
            """ The minimum distance between points to treat them as separate ones (-1 is KiCad default: 0.01 mm) """
            self.output = GS.def_global_output
            """ Name for the generated STEP file (%i='3D' %x='step') """
            self.download = True
            """ Downloads missing 3D models from KiCad git. Only applies to models in KISYS3DMOD """
            self.kicad_3d_url = 'https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/master/'
            """ Base URL for the KiCad 3D models """
        # Temporal dir used to store the downloaded files
        self._tmp_dir = None
        super().__init__()
        self._expand_id = '3D'
        self._expand_ext = 'step'

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, val):
        if (val not in ['grid', 'drill']) and (re.match(r'[-\d\.]+\s*,\s*[-\d\.]+\s*$', val) is None):
            raise KiPlotConfigurationError('Origin must be `grid` or `drill` or `X,Y`')
        self._origin = val

    def download_model(self, url, fname):
        """ Download the 3D model from the provided URL """
        logger.debug('Downloading `{}`'.format(url))
        r = requests.get(url, allow_redirects=True)
        if r.status_code != 200:
            logger.warning(W_FAILDL+'Failed to download `{}`'.format(url))
            return None
        if self._tmp_dir is None:
            self._tmp_dir = tempfile.mkdtemp()
            logger.debug('Using `{}` as temporal dir for downloaded files'.format(self._tmp_dir))
        dest = os.path.join(self._tmp_dir, fname)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(r.content)
        return dest

    def undo_3d_models_rename(self):
        """ Restores the file name for any renamed 3D module """
        for m in GS.board.GetModules():
            # Get the model references
            models = m.Models()
            models_l = []
            while not models.empty():
                models_l.append(models.pop())
            # Fix any changed path
            replaced = self.undo_3d_models_rep.get(m.GetReference())
            for i, m3d in enumerate(models_l):
                if m3d.m_Filename in self.undo_3d_models:
                    m3d.m_Filename = self.undo_3d_models[m3d.m_Filename]
                if replaced:
                    m3d.m_Filename = replaced[i]
            # Push the models back
            for model in models_l:
                models.push_front(model)

    def replace_models(self, models, new_model, c):
        """ Changes the 3D model using a provided model """
        logger.debug('Changing 3D models for '+c.ref)
        # Get the model references
        models_l = []
        while not models.empty():
            models_l.append(models.pop())
        # Check if we have more than one model
        c_models = len(models_l)
        if c_models > 1:
            new_model = new_model.split(',')
            c_replace = len(new_model)
            if c_models != c_replace:
                raise KiPlotConfigurationError('Found {} models in component {}, but {} replacements provided'.
                                               format(c_models, c, c_replace))
        else:
            new_model = [new_model]
        # Change the models
        replaced = []
        for i, m3d in enumerate(models_l):
            replaced.append(m3d.m_Filename)
            m3d.m_Filename = new_model[i]
        self.undo_3d_models_rep[c.ref] = replaced
        # Push the models back
        for model in models_l:
            models.push_front(model)

    def download_models(self):
        """ Check we have the 3D models.
            Inform missing models.
            Try to download the missing models """
        models_replaced = False
        # Load KiCad configuration so we can expand the 3D models path
        KiConf.init(GS.pcb_file)
        # List of models we already downloaded
        downloaded = set()
        self.undo_3d_models = {}
        # Look for all the footprints
        for m in GS.board.GetModules():
            ref = m.GetReference()
            # Extract the models (the iterator returns copies)
            models = m.Models()
            models_l = []
            while not models.empty():
                models_l.append(models.pop())
            # Look for all the 3D models for this footprint
            for m3d in models_l:
                full_name = KiConf.expand_env(m3d.m_Filename)
                if not os.path.isfile(full_name):
                    # Missing 3D model
                    if full_name not in downloaded:
                        logger.warning(W_MISS3D+'Missing 3D model for {}: `{}`'.format(ref, full_name))
                    if self.download and m3d.m_Filename.startswith('${KISYS3DMOD}/'):
                        # This is a model from KiCad, try to download it
                        fname = m3d.m_Filename[14:]
                        replace = None
                        if full_name in downloaded:
                            # Already downloaded
                            replace = os.path.join(self._tmp_dir, fname)
                        else:
                            # Download the model
                            url = self.kicad_3d_url+fname
                            replace = self.download_model(url, fname)
                            if replace:
                                # Successfully downloaded
                                downloaded.add(full_name)
                                self.undo_3d_models[replace] = m3d.m_Filename
                                # If this is a .wrl also download the .step
                                if url.endswith('.wrl'):
                                    url = url[:-4]+'.step'
                                    fname = fname[:-4]+'.step'
                                    self.download_model(url, fname)
                        if replace:
                            m3d.m_Filename = replace
                            models_replaced = True
            # Push the models back
            for model in models_l:
                models.push_front(model)
        return models_replaced

    def list_models(self):
        """ Get the list of 3D models """
        # Load KiCad configuration so we can expand the 3D models path
        KiConf.init(GS.pcb_file)
        models = set()
        # Look for all the footprints
        for m in GS.board.GetModules():
            # Look for all the 3D models for this footprint
            for m3d in m.Models():
                full_name = KiConf.expand_env(m3d.m_Filename)
                if os.path.isfile(full_name):
                    models.add(full_name)
        return list(models)

    def save_board(self, dir):
        """ Save the PCB to a temporal file """
        with NamedTemporaryFile(mode='w', suffix='.kicad_pcb', delete=False, dir=dir) as f:
            fname = f.name
        logger.debug('Storing modified PCB to `{}`'.format(fname))
        GS.board.Save(fname)
        return fname

    def filter_components(self, dir):
        self.undo_3d_models_rep = {}
        if not self._comps:
            # No variant/filter to apply
            if self.download_models():
                # Some missing components found and we downloaded them
                # Save the fixed board
                ret = self.save_board(dir)
                # Undo the changes
                self.undo_3d_models_rename()
                return ret
            return GS.pcb_file
        comps_hash = self.get_refs_hash()
        # Remove the 3D models for not fitted components
        rem_models = []
        for m in GS.board.GetModules():
            ref = m.GetReference()
            c = comps_hash.get(ref, None)
            if c:
                # The filter/variant knows about this component
                models = m.Models()
                if c.included and not c.fitted:
                    # Not fitted, remove the 3D model
                    rem_m_models = []
                    while not models.empty():
                        rem_m_models.append(models.pop())
                    rem_models.append(rem_m_models)
                else:
                    # Fitted
                    new_model = c.get_field_value(GS.global_3D_model_field)
                    if new_model:
                        # We will change the 3D model
                        self.replace_models(models, new_model, c)
        self.download_models()
        fname = self.save_board(dir)
        self.undo_3d_models_rename()
        # Undo the removing
        for m in GS.board.GetModules():
            ref = m.GetReference()
            c = comps_hash.get(ref, None)
            if c and c.included and not c.fitted:
                models = m.Models()
                restore = rem_models.pop(0)
                for model in restore:
                    models.push_front(model)
        return fname

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def run(self, output):
        super().run(output)
        # Make units explicit
        if self.metric_units:
            units = 'mm'
        else:
            units = 'in'
        # Base command with overwrite
        cmd = [KICAD2STEP, '-o', output, '-f']
        # Add user options
        if self.no_virtual:
            cmd.append('--no-virtual')
        if self.min_distance >= 0:
            cmd.extend(['--min-distance', "{}{}".format(self.min_distance, units)])
        if self.origin == 'drill':
            cmd.append('--drill-origin')
        elif self.origin == 'grid':
            cmd.append('--grid-origin')
        else:
            cmd.extend(['--user-origin', "{}{}".format(self.origin.replace(',', 'x'), units)])
        # The board
        board_name = self.filter_components(GS.pcb_dir)
        cmd.append(board_name)
        # Execute and inform is successful
        logger.debug('Executing: '+str(cmd))
        try:
            cmd_output = check_output(cmd, stderr=STDOUT)
        except CalledProcessError as e:
            logger.error('Failed to create Step file, error %d', e.returncode)
            if e.output:
                logger.debug('Output from command: '+e.output.decode())
            exit(KICAD2STEP_ERR)
        finally:
            # Remove the temporal PCB
            if board_name != GS.pcb_file:
                os.remove(board_name)
            # Remove the downloaded 3D models
            if self._tmp_dir:
                rmtree(self._tmp_dir)
        logger.debug('Output from command:\n'+cmd_output.decode())


@output_class
class STEP(BaseOutput):  # noqa: F821
    """ STEP (ISO 10303-21 Clear Text Encoding of the Exchange Structure)
        Exports the PCB as a 3D model.
        This is the most common 3D format for exchange purposes.
        This output is what you get from the 'File/Export/STEP' menu in pcbnew. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = STEPOptions
            """ [dict] Options for the `step` output """

    def get_dependencies(self):
        files = super().get_dependencies()
        files.extend(self.options.list_models())
        return files
