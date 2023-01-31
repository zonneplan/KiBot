# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from fnmatch import fnmatch
import os
import requests
from .EasyEDA.easyeda_3d import download_easyeda_3d_model
from .misc import W_MISS3D, W_FAILDL, W_DOWN3D, DISABLE_3D_MODEL_TEXT
from .gs import GS
from .optionable import Optionable
from .out_base import VariantOptions, BaseOutput
from .kicad.config import KiConf
from .macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger()


def do_expand_env(fname, used_extra, extra_debug):
    # Is it using ALIAS:xxxxx?
    force_used_extra = False
    if ':' in fname:
        ind = fname.index(':')
        alias_name = fname[:ind]
        rest = fname[ind+1:]
        if alias_name in KiConf.aliases_3D:
            # Yes, replace the alias
            fname = os.path.join(KiConf.aliases_3D[alias_name], rest)
            # Make sure the name we created is what kicad2step gets
            force_used_extra = True
            if extra_debug:
                logger.debug("- Replaced alias {} -> {}".format(alias_name+':'+rest, fname))
    full_name = KiConf.expand_env(fname, used_extra, ref_dir=GS.pcb_dir)
    if extra_debug:
        logger.debug("- Expanded {} -> {}".format(fname, full_name))
    if os.path.isfile(full_name) or ':' not in fname or GS.global_disable_3d_alias_as_env:
        full_name_cwd = KiConf.expand_env(fname, used_extra, ref_dir=os.getcwd())
        if os.path.isfile(full_name_cwd):
            full_name = full_name_cwd
            force_used_extra = True
        if force_used_extra:
            used_extra[0] = True
        return full_name
    # Look for ALIAS:file
    ind = fname.index(':')
    alias_name = fname[:ind]
    if len(alias_name) == 1:
        # Is a drive letter, not an alias
        return full_name
    rest = fname[ind+1:]
    new_fname = '${'+alias_name+'}'+os.path.sep+rest
    new_full_name = KiConf.expand_env(new_fname, used_extra)
    if extra_debug:
        logger.debug("- Expanded {} -> {}".format(new_fname, new_full_name))
    if os.path.isfile(new_full_name):
        used_extra[0] = True
        return new_full_name
    return full_name


class Base3DOptions(VariantOptions):
    def __init__(self):
        with document:
            self.no_virtual = False
            """ *Used to exclude 3D models for components with 'virtual' attribute """
            self.download = True
            """ *Downloads missing 3D models from KiCad git.
                Only applies to models in KISYS3DMOD and KICAD6_3DMODEL_DIR.
                They are downloaded to a temporal directory and discarded.
                If you want to cache the downloaded files specify a directory using the
                KIBOT_3D_MODELS environment variable """
            self.kicad_3d_url = 'https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/master/'
            """ Base URL for the KiCad 3D models """
        # Temporal dir used to store the downloaded files
        self._tmp_dir = None
        super().__init__()
        self._expand_id = '3D'

    def copy_options(self, ref):
        super().copy_options(ref)
        self.no_virtual = ref.no_virtual
        self.download = ref.download
        self.kicad_3d_url = ref.kicad_3d_url

    def download_model(self, url, fname, rel_dirs):
        """ Download the 3D model from the provided URL """
        dest = os.path.join(self._tmp_dir, fname)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        # Is already there?
        if os.path.isfile(dest):
            logger.debug('Using cached model `{}`'.format(dest))
            return dest
        logger.debug('Downloading `{}`'.format(url))
        failed = False
        try:
            r = requests.get(url, allow_redirects=True)
        except Exception:
            failed = True
        if failed or r.status_code != 200:
            logger.warning(W_FAILDL+'Failed to download `{}`'.format(url))
            return None
        with open(dest, 'wb') as f:
            f.write(r.content)
        return dest

    def wrl_name(self, name, force_wrl):
        """ Try to use the WRL version """
        if not force_wrl:
            return name
        nm, ext = os.path.splitext(name)
        if ext.lower() == '.wrl':
            return name
        nm += '.wrl'
        if os.path.isfile(nm):
            logger.debug('- Forcing WRL '+nm)
            return nm
        return name

    def try_download_kicad(self, model, full_name, downloaded, rel_dirs, force_wrl):
        if not (model.startswith('${KISYS3DMOD}/') or model.startswith('${KICAD6_3DMODEL_DIR}/')):
            return None
        # This is a model from KiCad, try to download it
        fname = model[model.find('/')+1:]
        replace = None
        if full_name in downloaded:
            # Already downloaded
            return os.path.join(self._tmp_dir, fname)
        # Download the model
        url = self.kicad_3d_url+fname
        replace = self.download_model(url, fname, rel_dirs)
        if not replace:
            return None
        # Successfully downloaded
        downloaded.add(full_name)
        # If this is a .wrl also download the .step
        if url.endswith('.wrl'):
            url = url[:-4]+'.step'
            fname = fname[:-4]+'.step'
            self.download_model(url, fname, rel_dirs)
        elif force_wrl:  # This should be a .step, so we download the wrl
            url = os.path.splitext(url)[0]+'.wrl'
            fname = os.path.splitext(fname)[0]+'.wrl'
            self.download_model(url, fname, rel_dirs)
        return replace

    def try_download_easyeda(self, model, full_name, downloaded, sch_comp, lcsc_field):
        if not lcsc_field or not sch_comp:
            return None
        lcsc_id = sch_comp.get_field_value(lcsc_field)
        if not lcsc_id:
            return None
        fname = os.path.basename(model)
        cache_name = os.path.join(self._tmp_dir, fname)
        if full_name in downloaded:
            # Already downloaded
            return cache_name
        if os.path.isfile(cache_name):
            downloaded.add(full_name)
            logger.debug('Using cached model `{}`'.format(cache_name))
            return cache_name
        logger.debug('- Trying to download {} component as {}/{}'.format(lcsc_id, self._tmp_dir, fname))
        replace = download_easyeda_3d_model(lcsc_id, self._tmp_dir, fname)
        if not replace:
            return None
        # Successfully downloaded
        downloaded.add(full_name)
        return replace

    def download_models(self, rename_filter=None, rename_function=None, rename_data=None, force_wrl=False, all_comps=None):
        """ Check we have the 3D models.
            Inform missing models.
            Try to download the missing models
            Stores changes in self.undo_3d_models_rep """
        models_replaced = False
        # Load KiCad configuration so we can expand the 3D models path
        KiConf.init(GS.pcb_file)
        # List of models we already downloaded
        downloaded = set()
        # For the mode where we copy the 3D models
        source_models = set()
        is_copy_mode = rename_filter is not None
        rel_dirs = getattr(rename_data, 'rel_dirs', [])
        extra_debug = GS.debug_level > 3
        # Get a list of components in the schematic. Enables downloading LCSC parts.
        if all_comps is None and GS.sch_file:
            GS.load_sch()
            all_comps = GS.sch.get_components()
        if all_comps is None:
            all_comps = []
        all_comps_hash = {c.ref: c for c in all_comps}
        # Find the LCSC field
        lcsc_field = self.solve_field_name('_field_lcsc_part', empty_when_none=True)
        # Find a place to store the downloaded models
        if self._tmp_dir is None:
            self._tmp_dir = os.environ.get('KIBOT_3D_MODELS')
            if self._tmp_dir is None:
                self._tmp_dir = os.path.join(os.path.expanduser('~'), '.cache', 'kibot', '3d')
            else:
                self._tmp_dir = os.path.abspath(self._tmp_dir)
            rel_dirs.append(self._tmp_dir)
            logger.debug('Using `{}` as dir for downloaded 3D models'.format(self._tmp_dir))
        # Look for all the footprints
        for m in GS.get_modules():
            ref = m.GetReference()
            sch_comp = all_comps_hash.get(ref, None)
            # Extract the models (the iterator returns copies)
            models = m.Models()
            models_l = []
            while not models.empty():
                models_l.append(models.pop())
            # Look for all the 3D models for this footprint
            for m3d in models_l:
                if m3d.m_Filename.endswith(DISABLE_3D_MODEL_TEXT):
                    # Skip models we intentionally disabled using a bogus name
                    if extra_debug:
                        logger.debug("- Skipping {} (disabled)".format(m3d.m_Filename))
                    continue
                if is_copy_mode and not fnmatch(m3d.m_Filename, rename_filter):
                    # Skip filtered footprints
                    continue
                used_extra = [False]
                full_name = do_expand_env(m3d.m_Filename, used_extra, extra_debug)
                if not os.path.isfile(full_name):
                    logger.debugl(2, 'Missing 3D model file {} ({})'.format(full_name, m3d.m_Filename))
                    # Missing 3D model
                    if self.download:
                        replace = self.try_download_kicad(m3d.m_Filename, full_name, downloaded, rel_dirs, force_wrl)
                        if replace is None:
                            replace = self.try_download_easyeda(m3d.m_Filename, full_name, downloaded, sch_comp, lcsc_field)
                        if replace:
                            source_models.add(replace)
                            old_name = m3d.m_Filename
                            new_name = (self.wrl_name(replace, force_wrl) if not is_copy_mode else
                                        rename_function(rename_data, replace))
                            self.undo_3d_models[new_name] = old_name
                            m3d.m_Filename = new_name
                            models_replaced = True
                    if full_name not in downloaded:
                        logger.warning(W_MISS3D+'Missing 3D model for {}: `{}`'.format(ref, full_name))
                else:  # File was found
                    if used_extra[0] or is_copy_mode:
                        # The file is there, but we got it expanding a user defined text
                        # This is completely valid for KiCad, but kicad2step doesn't support it
                        source_models.add(full_name)
                        old_name = m3d.m_Filename
                        new_name = (self.wrl_name(full_name, force_wrl) if not is_copy_mode else
                                    rename_function(rename_data, full_name))
                        self.undo_3d_models[new_name] = old_name
                        m3d.m_Filename = new_name
                        if not models_replaced and extra_debug:
                            logger.debug('- Modifying models with text vars')
                        models_replaced = True
            # Push the models back
            for model in models_l:
                models.push_front(model)
        if downloaded:
            logger.warning(W_DOWN3D+' {} 3D models downloaded'.format(len(downloaded)))
        return models_replaced if not is_copy_mode else list(source_models)

    def list_models(self, even_missing=False):
        """ Get the list of 3D models """
        # Load KiCad configuration so we can expand the 3D models path
        KiConf.init(GS.pcb_file)
        models = set()
        # Look for all the footprints
        for m in GS.get_modules():
            # Look for all the 3D models for this footprint
            for m3d in m.Models():
                full_name = KiConf.expand_env(m3d.m_Filename)
                if even_missing or os.path.isfile(full_name):
                    models.add(full_name)
        return list(models)

    def filter_components(self, highlight=None, force_wrl=False):
        if not self._comps:
            # No variant/filter to apply
            if self.download_models(force_wrl=force_wrl):
                # Some missing components found and we downloaded them
                # Save the fixed board
                ret = self.save_tmp_board()
                # Undo the changes done during download
                self.undo_3d_models_rename(GS.board)
                return ret
            return GS.pcb_file
        self.filter_pcb_components(do_3D=True, do_2D=True, highlight=highlight)
        self.download_models(force_wrl=force_wrl, all_comps=self._comps)
        fname = self.save_tmp_board()
        self.unfilter_pcb_components(do_3D=True, do_2D=True)
        return fname

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def remove_temporals(self):
        super().remove_temporals()
        self._tmp_dir = None


class Base3DOptionsWithHL(Base3DOptions):
    """ 3D options including which components will be displayed and highlighted """
    def __init__(self):
        with document:
            self.show_components = Optionable
            """ *[list(string)|string=all] [none,all] List of components to draw, can be also a string for `none` or `all`.
                Unlike the `pcbdraw` output, the default is `all` """
            self.highlight = Optionable
            """ [list(string)=[]] List of components to highlight """
            self.highlight_padding = 1.5
            """ [0,1000] How much the highlight extends around the component [mm] """
            self.highlight_on_top = False
            """ Highlight over the component (not under) """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self._filters_to_expand = False
        # List of components
        self._show_all_components = False
        self._show_components_raw = self.show_components
        if isinstance(self.show_components, str):
            if self.show_components == 'all':
                self._show_all_components = True
            self.show_components = []
        elif isinstance(self.show_components, type):
            # Default is all
            self._show_all_components = True
        else:  # a list
            self.show_components = self.solve_kf_filters(self.show_components)
        # Highlight
        if isinstance(self.highlight, type):
            self.highlight = None
        else:
            self.highlight = self.solve_kf_filters(self.highlight)

    def copy_options(self, ref):
        """ Copy its options from another similar object """
        super().copy_options(ref)
        self.show_components = ref.show_components
        self.highlight = ref.highlight
        self.highlight_padding = ref.highlight_padding
        self.highlight_on_top = ref.highlight_on_top
        self._filters_to_expand = ref._filters_to_expand
        self._show_all_components = ref._show_all_components


class Base3D(BaseOutput):
    def __init__(self):
        super().__init__()

    def get_dependencies(self):
        files = super().get_dependencies()
        files.extend(self.options.list_models())
        return files
