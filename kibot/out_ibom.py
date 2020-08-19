import os
from subprocess import (check_output, STDOUT, CalledProcessError)
from .misc import (CMD_IBOM, URL_IBOM, BOM_ERROR)
from .gs import (GS)
from .kiplot import (check_script)
from .optionable import BaseOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class IBoMOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ Filename for the output, use '' to use the IBoM filename (%i=ibom, %x=html) """
            self.dark_mode = False
            """ Default to dark mode """
            self.hide_pads = False
            """ Hide footprint pads by default """
            self.show_fabrication = False
            """ Show fabrication layer by default """
            self.hide_silkscreen = False
            """ Hide silkscreen by default """
            self.highlight_pin1 = False
            """ Highlight pin1 by default """
            self.no_redraw_on_drag = False
            """ Do not redraw pcb on drag by default """
            self.board_rotation = 0
            """ Board rotation in degrees (-180 to 180). Will be rounded to multiple of 5 """
            self.checkboxes = 'Sourced,Placed'
            """ Comma separated list of checkbox columns """
            self.bom_view = 'left-right'
            """ [bom-only,left-right,top-bottom] Default BOM view """
            self.layer_view = 'FB'
            """ [F,FB,B] Default layer view """
            self.name_format = 'ibom'
            """ Output file name format supports substitutions:
                %f : original pcb file name without extension.
                %p : pcb/project title from pcb metadata.
                %c : company from pcb metadata.
                %r : revision from pcb metadata.
                %d : pcb date from metadata if available, file modification date otherwise.
                %D : bom generation date.
                %T : bom generation time.
                Extension .html will be added automatically.
                Note that this name is used only when output is '' """
            self.include_tracks = False
            """ Include track/zone information in output. F.Cu and B.Cu layers only """
            self.include_nets = False
            """ Include netlist information in output. """
            self.sort_order = 'C,R,L,D,U,Y,X,F,SW,A,~,HS,CNN,J,P,NT,MH'
            """ Default sort order for components. Must contain '~' once """
            self.blacklist = ''
            """ List of comma separated blacklisted components or prefixes with *. E.g. 'X1,MH*' """
            self.no_blacklist_virtual = False
            """ Do not blacklist virtual components """
            self.blacklist_empty_val = False
            """ Blacklist components with empty value """
            self.netlist_file = ''
            """ Path to netlist or xml file """
            self.extra_fields = ''
            """ Comma separated list of extra fields to pull from netlist or xml file """
            self.normalize_field_case = False
            """ Normalize extra field name case. E.g. 'MPN' and 'mpn' will be considered the same field """
            self.variant_field = ''
            """ Name of the extra field that stores board variant for component """
            self.variants_whitelist = ''
            """ List of board variants to include in the BOM """
            self.variants_blacklist = ''
            """ List of board variants to exclude from the BOM """
            self.dnp_field = ''
            """ Name of the extra field that indicates do not populate status. Components with this field not empty will be
                blacklisted """
        super().__init__()

    def run(self, output_dir, board):
        check_script(CMD_IBOM, URL_IBOM)
        logger.debug('Doing Interactive BoM')
        # Tell ibom we don't want to use the screen
        os.environ['INTERACTIVE_HTML_BOM_NO_DISPLAY'] = ''
        cmd = [CMD_IBOM, GS.pcb_file, '--dest-dir', output_dir, '--no-browser', ]
        # Solve the output name
        output = None
        if self.output:
            output = self.expand_filename(output_dir, self.output, 'ibom', 'html')
            self.name_format = 'ibom'
            cur = os.path.join(output_dir, 'ibom.html')
        # Convert attributes into options
        for k, v in self.get_attrs_gen():
            if not v or k == 'output':
                continue
            cmd.append(BaseOutput.attr2longopt(k))  # noqa: F821
            if not isinstance(v, bool):  # must be str/(int, float)
                cmd.append(str(v))
        # Run the command
        logger.debug('Running: '+str(cmd))
        try:
            cmd_output = check_output(cmd, stderr=STDOUT)
            cmd_output_dec = cmd_output.decode()
            # IBoM returns 0 for this error!!!
            if 'ERROR Parsing failed' in cmd_output_dec:
                raise CalledProcessError(1, cmd, cmd_output)
        except CalledProcessError as e:
            logger.error('Failed to create BoM, error %d', e.returncode)
            if e.output:
                logger.debug('Output from command: '+e.output.decode())
            exit(BOM_ERROR)
        logger.debug('Output from command:\n'+cmd_output_dec+'\n')
        if output:
            logger.debug('Renaming output file: {} -> {}'.format(cur, output))
            os.rename(cur, output)


@output_class
class IBoM(BaseOutput):  # noqa: F821
    """ IBoM (Interactive HTML BoM)
        Generates an interactive web page useful to identify the position of the components in the PCB.
        For more information: https://github.com/INTI-CMNB/InteractiveHtmlBom
        This output is what you get from the InteractiveHtmlBom plug-in (pcbnew). """
    def __init__(self):
        super().__init__()
        with document:
            self.options = IBoMOptions
            """ [dict] Options for the `ibom` output """
