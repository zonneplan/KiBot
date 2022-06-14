# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# The Assembly image is a composition from Pixlok and oNline Web Fonts
# The rest are KiCad icons
import os
import subprocess
import pprint
from shutil import copy2, which
from math import ceil
from struct import unpack
from tempfile import NamedTemporaryFile
from .gs import GS
from .optionable import BaseOptions
from .kiplot import config_output, get_output_dir
from .misc import W_NOTYET, W_MISSTOOL, TRY_INSTALL_CHECK, ToolDependencyRole, ToolDependency
from .registrable import RegOutput, RegDependency
from .macros import macros, document, output_class  # noqa: F401
from . import log, __version__

SVGCONV = 'rsvg-convert'
CONVERT = 'convert'
PS2IMG = 'ghostscript'
RegDependency.register(ToolDependency('navigate_results', 'RSVG tools',
                                      'https://cran.r-project.org/web/packages/rsvg/index.html', deb='librsvg2-bin',
                                      command=SVGCONV,
                                      roles=[ToolDependencyRole(desc='Create outputs preview'),
                                             ToolDependencyRole(desc='Create PNG icons')]))
RegDependency.register(ToolDependency('navigate_results', 'Ghostscript', 'https://www.ghostscript.com/',
                                      url_down='https://github.com/ArtifexSoftware/ghostpdl-downloads/releases',
                                      roles=ToolDependencyRole(desc='Create outputs preview')))
RegDependency.register(ToolDependency('navigate_results', 'ImageMagick', 'https://imagemagick.org/', command='convert',
                                      roles=ToolDependencyRole(desc='Create outputs preview')))
logger = log.get_logger()
CAT_IMAGE = {'PCB': 'pcbnew',
             'Schematic': 'eeschema',
             'Compress': 'zip',
             'fabrication': 'fabrication',
             'export': 'export',
             'assembly': 'assembly_simple',
             'repair': 'repair',
             'docs': 'project',
             'BoM': 'bom',
             '3D': '3d',
             'gerber': 'gerber',
             'drill': 'load_drill'}
EXT_IMAGE = {'gbr': 'file_gbr',
             'gtl': 'file_gbr',
             'gtp': 'file_gbr',
             'gbo': 'file_gbr',
             'gto': 'file_gbr',
             'gbs': 'file_gbr',
             'gbl': 'file_gbr',
             'gts': 'file_gbr',
             'gml': 'file_gbr',
             'gm1': 'file_gbr',
             'gbrjob': 'file_gerber_job',
             'brd': 'file_brd',
             'bz2': 'file_bz2',
             'dxf': 'file_dxf',
             'cad': 'file_cad',
             'drl': 'file_drl',
             'pdf': 'file_pdf',
             'txt': 'file_txt',
             'pos': 'file_pos',
             'csv': 'file_csv',
             'svg': 'file_svg',
             'eps': 'file_eps',
             'png': 'file_png',
             'jpg': 'file_jpg',
             'plt': 'file_plt',
             'ps': 'file_ps',
             'rar': 'file_rar',
             'step': 'file_stp',
             'stp': 'file_stp',
             'html': 'file_html',
             'xml': 'file_xml',
             'tsv': 'file_tsv',
             'xlsx': 'file_xlsx',
             'xyrs': 'file_xyrs',
             'xz': 'file_xz',
             'gz': 'file_gz',
             'tar': 'file_tar',
             'zip': 'file_zip'}
for i in range(31):
    n = str(i)
    EXT_IMAGE['gl'+n] = 'file_gbr'
    EXT_IMAGE['g'+n] = 'file_gbr'
    EXT_IMAGE['gp'+n] = 'file_gbr'
CAT_REP = {'PCB': ['pdf_pcb_print', 'svg_pcb_print', 'pcb_print'],
           'Schematic': ['pdf_sch_print', 'svg_sch_print']}
BIG_ICON = 256
MID_ICON = 64
OUT_COLS = 12
BIG_2_MID_REL = int(ceil(BIG_ICON/MID_ICON))
IMAGEABLES_SIMPLE = {'png', 'jpg'}
IMAGEABLES_GS = {'pdf', 'eps', 'ps'}
IMAGEABLES_SVG = {'svg'}
STYLE = """
.cat-table { margin-left: auto; margin-right: auto; }
.cat-table td { padding: 20px 24px; }
.nav-table { margin-left: auto; margin-right: auto; }
.nav-table td { padding: 20px 24px; }
.output-table {
  width: 1280px;
  margin-left: auto;
  margin-right: auto;
  border-collapse:
  collapse;
  margin-top: 5px;
  margin-bottom: 4em;
  font-size: 0.9em;
  font-family: sans-serif;
  min-width: 400px;
  border-radius: 5px 5px 0 0;
  overflow: hidden;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
}
.output-table thead tr { background-color: #0e4e8e; color: #ffffff; text-align: left; }
.output-table th { padding: 10px 12px; }
.output-table td { padding: 5px 7px; }
.out-cell { width: 128px; text-align: center }
.out-img { text-align: center; margin-left: auto; margin-right: auto; }
.cat-img { text-align: center; margin-left: auto; margin-right: auto; }
.td-small { text-align: center; font-size: 0.6em; }
.td-normal { text-align: center; }
.generator { text-align: right; font-size: 0.6em; }
a:link, a:visited { text-decoration: none;}
a:hover, a:active { text-decoration: underline;}
"""


def _run_command(cmd):
    logger.debug('- Executing: '+str(cmd))
    try:
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error('Failed to run %s, error %d', cmd[0], e.returncode)
        if e.output:
            logger.debug('Output from command: '+e.output.decode())
        return False
    if cmd_output.strip():
        logger.debug('- Output from command:\n'+cmd_output.decode())
    return True


def svg_to_png(svg_file, png_file, width):
    cmd = [SVGCONV, '-w', str(width), '-f', 'png', '-o', png_file, svg_file]
    return _run_command(cmd)


def get_png_size(file):
    with open(file, 'rb') as f:
        s = f.read()
    if not (s[:8] == b'\x89PNG\r\n\x1a\n' and (s[12:16] == b'IHDR')):
        return 0, 0
    w, h = unpack('>LL', s[16:24])
    return int(w), int(h)


class Navigate_ResultsOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=html, %x=navigate) """
            self.link_from_root = ''
            """ *The name of a file to create at the main output directory linking to the home page """
        super().__init__()
        self._expand_id = 'navigate'
        self._expand_ext = 'html'

    def add_to_tree(self, cat, out, o_tree):
        # Add `out` to `o_tree` in the `cat` category
        cat = cat.split('/')
        node = o_tree
        for c in cat:
            if c not in node:
                # New one
                node[c] = {}
            node = node[c]
        node[out.name] = out

    def copy(self, img, width):
        """ Copy an SVG icon to the images/ dir.
            Tries to convert it to PNG. """
        img_w = "{}_{}".format(img, width)
        if img_w in self.copied_images:
            # Already copied, just return its name
            return self.copied_images[img_w]
        src = os.path.join(self.img_src_dir, 'images', img+'.svg')
        dst = os.path.join(self.out_dir, 'images', img_w)
        id = img_w
        if self.svg2png_avail and svg_to_png(src, dst+'.png', width):
            img_w += '.png'
        else:
            copy2(src, dst+'.svg')
            img_w += '.svg'
        name = os.path.join('images', img_w)
        self.copied_images[id] = name
        return name

    def can_be_converted(self, ext):
        if ext in IMAGEABLES_SVG and not self.svg2png_avail:
            logger.warning(W_MISSTOOL+"Missing SVG to PNG converter: "+SVGCONV)
            logger.warning(W_MISSTOOL+TRY_INSTALL_CHECK)
            return False
        if ext in IMAGEABLES_GS and not self.ps2img_avail:
            logger.warning(W_MISSTOOL+"Missing PS/PDF to PNG converter: "+PS2IMG)
            logger.warning(W_MISSTOOL+TRY_INSTALL_CHECK)
            return False
        if ext in IMAGEABLES_SIMPLE and not self.convert_avail:
            logger.warning(W_MISSTOOL+"Missing Imagemagick converter: "+CONVERT)
            logger.warning(W_MISSTOOL+TRY_INSTALL_CHECK)
            return False
        return ext in IMAGEABLES_SVG or ext in IMAGEABLES_GS or ext in IMAGEABLES_SIMPLE

    def get_image_for_cat(self, cat):
        img = None
        # Check if we have an output that can represent this category
        if cat in CAT_REP and self.convert_avail:
            outs_rep = CAT_REP[cat]
            rep_file = None
            # Look in all outputs
            for o in RegOutput.get_outputs():
                # Is this one that can be used to represent it?
                if o.type in outs_rep:
                    out_dir = get_output_dir(o.dir, o, dry=True)
                    targets = o.get_targets(out_dir)
                    # Look the output targets
                    for tg in targets:
                        ext = os.path.splitext(tg)[1][1:].lower()
                        # Can be converted to an image?
                        if os.path.isfile(tg) and self.can_be_converted(ext):
                            rep_file = tg
                            break
                    if rep_file:
                        break
            if rep_file:
                cat, _ = self.get_image_for_file(rep_file, cat, no_icon=True)
                return cat
        if cat in CAT_IMAGE:
            img = self.copy(CAT_IMAGE[cat], BIG_ICON)
            cat_img = '<img src="{}" alt="{}" width="{}" height="{}">'.format(img, cat, BIG_ICON, BIG_ICON)
            cat = ('<table class="cat-img"><tr><td>{}<br>{}</td></tr></table>'.
                   format(cat_img, cat))
        return cat

    def compose_image(self, file, ext, img, out_name, no_icon=False):
        if not os.path.isfile(file):
            logger.warning(W_NOTYET+"{} not yet generated, using an icon".format(os.path.relpath(file)))
            return False, None, None
        # Create a unique name using the output name and the generated file name
        bfname = os.path.splitext(os.path.basename(file))[0]
        fname = os.path.join(self.out_dir, 'images', out_name+'_'+bfname+'.png')
        # Full path for the icon image
        icon = os.path.join(self.out_dir, img)
        if ext == 'pdf':
            # Only page 1
            file += '[0]'
        if ext == 'svg':
            with NamedTemporaryFile(mode='w', suffix='.png', delete=False) as f:
                tmp_name = f.name
            logger.debug('Temporal convert: {} -> {}'.format(file, tmp_name))
            if not svg_to_png(file, tmp_name, BIG_ICON):
                return False, None, None
            file = tmp_name
        cmd = [CONVERT, file,
               # Size for the big icons (width)
               '-resize', str(BIG_ICON)+'x']
        if not no_icon:
            cmd.extend([  # Add the file type icon
                        icon,
                        # At the bottom right
                        '-gravity', 'south-east',
                        # This is a composition, not 2 images
                        '-composite'])
        cmd.append(fname)
        res = _run_command(cmd)
        if ext == 'svg':
            logger.debug('Removing temporal {}'.format(tmp_name))
            os.remove(tmp_name)
        return res, fname, os.path.relpath(fname, start=self.out_dir)

    def get_image_for_file(self, file, out_name, no_icon=False):
        ext = os.path.splitext(file)[1][1:].lower()
        wide = False
        # Copy the icon for this file extension
        img = self.copy(EXT_IMAGE.get(ext, 'unknown'), MID_ICON)
        # Full name for the file
        file_full = file
        # Just the file, to display it
        file = os.path.basename(file)
        # The icon size
        height = width = MID_ICON
        # Check if this file can be represented by an image
        if self.can_be_converted(ext):
            # Try to compose the image of the file with the icon
            ok, fimg, new_img = self.compose_image(file_full, ext, img, 'cat_'+out_name, no_icon)
            if ok:
                # It was converted, replace the icon by the composited image
                img = new_img
                # Compute its size
                width, height = get_png_size(fimg)
                # We are using the big size
                wide = True
        # Now add the image with its file name as caption
        ext_img = '<img src="{}" alt="{}" width="{}" height="{}">'.format(img, file, width, height)
        file = ('<table class="out-img"><tr><td>{}</td></tr><tr><td class="{}">{}</td></tr></table>'.
                format(ext_img, 'td-normal' if no_icon else 'td-small', out_name if no_icon else file))
        return file, wide

    def add_back_home(self, f, prev):
        if prev is not None:
            prev += '.html'
            f.write('<table class="nav-table">')
            f.write(' <tr>')
            f.write('  <td><a href="{}"><img src="{}" width="{}" height="{}" alt="go back"></a></td>'.
                    format(prev, self.back_img, MID_ICON, MID_ICON))
            f.write('  <td><a href="{}"><img src="{}" width="{}" height="{}" alt="go home"></a></td>'.
                    format(self.home, self.home_img, MID_ICON, MID_ICON))
            f.write(' </tr>')
            f.write('</table>')
        f.write('<p class="generator">Generated by <a href="https://github.com/INTI-CMNB/KiBot/">KiBot</a> v{}</p>'.
                format(__version__))

    def write_head(self, f, title):
        f.write('<!DOCTYPE html>\n')
        f.write('<html lang="en">\n')
        f.write('<head>\n')
        f.write(' <title>{}</title>\n'.format(title if title else 'Main page'))
        f.write(' <meta charset="UTF-8">\n')  # UTF-8 encoding for unicode support
        f.write(' <link rel="stylesheet" href="styles.css">\n')
        f.write(' <link rel="icon" href="favicon.ico">\n')
        f.write('</head>\n')
        f.write('<body>\n')

    def generate_cat_page_for(self, name, node, prev, category):
        logger.debug('- Categories: '+str(node.keys()))
        with open(os.path.join(self.out_dir, name), 'wt') as f:
            self.write_head(f, category)
            name, ext = os.path.splitext(name)
            # Limit to 5 categories by row
            c_cats = len(node)
            rows = ceil(c_cats/5.0)
            by_row = c_cats/rows
            acc = 0
            f.write('<table class="cat-table">\n<tr>\n')
            for cat, content in node.items():
                if not isinstance(content, dict):
                    continue
                if acc >= by_row:
                    # Flush the table and create another
                    acc = 0
                    f.write('</tr>\n</table>\n<table class="cat-table">\n<tr>\n')
                pname = name+'_'+cat+ext
                self.generate_page_for(content, pname, name, category+'/'+cat)
                f.write(' <td><a href="{}">{}</a></td>\n'.format(pname, self.get_image_for_cat(cat)))
                acc += 1
            f.write('</tr>\n</table>\n')
            self.generate_outputs(f, node)
            self.add_back_home(f, prev)
            f.write('</body>\n</html>\n')

    def generate_outputs(self, f, node):
        for oname, out in node.items():
            if isinstance(out, dict):
                continue
            f.write('<table class="output-table">\n')
            out_name = oname.replace(' ', '_')
            oname = oname.replace('_', ' ')
            oname = oname[0].upper()+oname[1:]
            if out.comment:
                oname += ': '+out.comment
            f.write('<thead><tr><th colspan="{}">{}</th></tr></thead>\n'.format(OUT_COLS, oname))
            out_dir = get_output_dir(out.dir, out, dry=True)
            f.write('<tbody><tr>\n')
            targets = out.get_targets(out_dir)
            if len(targets) == 1:
                tg_rel = os.path.relpath(os.path.abspath(targets[0]), start=self.out_dir)
                img, _ = self.get_image_for_file(targets[0], out_name)
                f.write('<td class="out-cell" colspan="{}"><a href="{}">{}</a></td>\n'.
                        format(OUT_COLS, tg_rel, img))
            else:
                c = 0
                for tg in targets:
                    if c == OUT_COLS:
                        f.write('</tr>\n<tr>\n')
                        c = 0
                    tg_rel = os.path.relpath(os.path.abspath(tg), start=self.out_dir)
                    img, wide = self.get_image_for_file(tg, out_name)
                    # Check if we need to break this row
                    span = 1
                    if wide:
                        span = BIG_2_MID_REL
                        remain = OUT_COLS-c
                        if span > remain:
                            f.write('<td class="out-cell" colspan="{}"></td></tr>\n<tr>\n'.format(remain))
                    # Add a new cell
                    f.write('<td class="out-cell" colspan="{}"><a href="{}">{}</a></td>\n'.format(span, tg_rel, img))
                    c = c+span
                if c < OUT_COLS:
                    f.write('<td class="out-cell" colspan="{}"></td>\n'.format(OUT_COLS-c))
            f.write('</tr>\n')
            # This row is just to ensure we have at least 1 cell in each column
            f.write('<tr>\n')
            for _ in range(OUT_COLS):
                f.write('<td></td>\n')
            f.write('</tr>\n')
            f.write('</tbody>\n')
            f.write('</table>\n')

    def generate_end_page_for(self, name, node, prev, category):
        logger.debug('- Outputs: '+str(node.keys()))
        with open(os.path.join(self.out_dir, name), 'wt') as f:
            self.write_head(f, category)
            name, ext = os.path.splitext(name)
            self.generate_outputs(f, node)
            self.add_back_home(f, prev)
            f.write('</body>\n</html>\n')

    def generate_page_for(self, node, name, prev=None, category=''):
        logger.debug('Generating page for '+name)
        if isinstance(list(node.values())[0], dict):
            self.generate_cat_page_for(name, node, prev, category)
        else:
            self.generate_end_page_for(name, node, prev, category)

    def run(self, name):
        self.out_dir = os.path.dirname(name)
        self.img_src_dir = os.path.dirname(__file__)
        self.img_dst_dir = os.path.join(self.out_dir, 'images')
        os.makedirs(self.img_dst_dir, exist_ok=True)
        self.copied_images = {}
        name = os.path.basename(name)
        # Create a tree with all the outputs
        o_tree = {}
        for o in RegOutput.get_outputs():
            config_output(o)
            cat = o.category
            if cat is None:
                continue
            if isinstance(cat, str):
                cat = [cat]
            for c in cat:
                self.add_to_tree(c, o, o_tree)
        logger.debug('Collected outputs:\n'+pprint.pformat(o_tree))
        with open(os.path.join(self.out_dir, 'styles.css'), 'wt') as f:
            f.write(STYLE)
        self.svg2png_avail = which(SVGCONV) is not None
        self.convert_avail = which(CONVERT) is not None
        self.ps2img_avail = which(PS2IMG) is not None
        # Create the pages
        self.home = name
        self.back_img = self.copy('back', MID_ICON)
        self.home_img = self.copy('home', MID_ICON)
        copy2(os.path.join(self.img_src_dir, 'images', 'favicon.ico'), os.path.join(self.out_dir, 'favicon.ico'))
        self.generate_page_for(o_tree, name)
        # Link it?
        if self.link_from_root:
            redir_file = os.path.join(GS.out_dir, self.link_from_root)
            rel_start = os.path.relpath(os.path.join(self.out_dir, name), start=GS.out_dir)
            logger.debug('Creating redirector: {} -> {}'.format(redir_file, rel_start))
            with open(redir_file, 'wt') as f:
                f.write('<html>\n<head>\n<meta http-equiv="refresh" content="0; {}"/>'.format(rel_start))
                f.write('</head>\n</html>')


@output_class
class Navigate_Results(BaseOutput):  # noqa: F821
    """ Navigate Results
        Generates a web page to navigate the generated outputs """
    def __init__(self):
        super().__init__()
        # Make it low priority so it gets created after all the other outputs
        self.priority = 10
        with document:
            self.options = Navigate_ResultsOptions
            """ *[dict] Options for the `navigate_results` output """
        # The help is inherited and already mentions the default priority
        self.fix_priority_help()

    @staticmethod
    def get_conf_examples(name, layers, templates):
        outs = BaseOutput.simple_conf_examples(name, 'Web page to browse the results', 'Browse')  # noqa: F821
        outs[0]['options'] = {'link_from_root': 'index.html'}
        return outs
