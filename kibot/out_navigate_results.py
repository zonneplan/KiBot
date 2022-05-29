# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# The Assembly image is a composition from Pixlok and oNline Web Fonts
# The rest are KiCad icons
import os
import subprocess
from shutil import copy2, which
from math import ceil
from .gs import GS
import pprint
from .optionable import BaseOptions
from .kiplot import config_output, get_output_dir
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log, __version__

logger = log.get_logger()
CAT_IMAGE = {'PCB': 'pcbnew',
             'Schematic': 'eeschema',
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
             'step': 'file_stp',
             'stp': 'file_stp',
             'html': 'file_html',
             'xml': 'file_xml',
             'tsv': 'file_tsv',
             'xlsx': 'file_xlsx',
             'xyrs': 'file_xyrs'}
for i in range(31):
    n = str(i)
    EXT_IMAGE['gl'+n] = 'file_gbr'
    EXT_IMAGE['g'+n] = 'file_gbr'
    EXT_IMAGE['gp'+n] = 'file_gbr'
BIG_ICON = 256
MID_ICON = 64
OUT_COLS = 10
SVGCONV = 'rsvg-convert'
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


class Navigate_ResultsOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ Filename for the output (%i=html, %x=navigate) """
            self.link_from_root = ''
            """ The name of a file to create at the main output directory linking to the home page """
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
        src = os.path.join(self.img_src_dir, 'images', img+'.svg')
        dst = os.path.join(self.out_dir, 'images', img)
        if self.svg2png_avail and svg_to_png(src, dst+'.png', width):
            img += '.png'
        else:
            copy2(src, dst+'.svg')
            img += '.svg'
        return os.path.join('images', img)

    def get_image_for_cat(self, cat):
        if cat in CAT_IMAGE:
            img = self.copy(CAT_IMAGE[cat], BIG_ICON)
            cat_img = '<img src="{}" alt="{}" width="{}" height="{}">'.format(img, cat, BIG_ICON, BIG_ICON)
            cat = ('<table class="cat-img"><tr><td>{}<br>{}</td></tr></table>'.
                   format(cat_img, cat))
        return cat

    def get_image_for_file(self, file):
        ext = os.path.splitext(file)[1][1:].lower()
        img = self.copy(EXT_IMAGE.get(ext, 'unknown'), MID_ICON)
        ext_img = '<img src="{}" alt="{}" width="{}" height="{}">'.format(img, file, MID_ICON, MID_ICON)
        file = ('<table class="out-img"><tr><td>{}</td></tr><tr><td class="td-small">{}</td></tr></table>'.
                format(ext_img, file))
        return file

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
                if acc >= by_row:
                    # Flush the table and create another
                    acc = 0
                    f.write('</tr>\n</table>\n<table class="cat-table">\n<tr>\n')
                pname = name+'_'+cat+ext
                self.generate_page_for(content, pname, name, category+'/'+cat)
                f.write(' <td><a href="{}">{}</a></td>\n'.format(pname, self.get_image_for_cat(cat)))
                acc += 1
            f.write('</tr>\n</table>\n')
            self.add_back_home(f, prev)
            f.write('</body>\n</html>\n')

    def generate_end_page_for(self, name, node, prev, category):
        logger.debug('- Outputs: '+str(node.keys()))
        with open(os.path.join(self.out_dir, name), 'wt') as f:
            self.write_head(f, category)
            name, ext = os.path.splitext(name)
            for oname, out in node.items():
                f.write('<table class="output-table">\n')
                oname = oname.replace('_', ' ')
                oname = oname[0].upper()+oname[1:]
                if out.comment:
                    oname += ': '+out.comment
                f.write('<thead><tr><th colspan="{}">{}</th></tr></thead>\n'.format(OUT_COLS, oname))
                config_output(out)
                out_dir = get_output_dir(out.dir, out, dry=True)
                f.write('<tbody><tr>\n')
                targets = out.get_targets(out_dir)
                if len(targets) == 1:
                    tg = os.path.relpath(os.path.abspath(targets[0]), start=self.out_dir)
                    f.write('<td class="out-cell" colspan="{}"><a href="{}">{}</a></td>\n'.
                            format(OUT_COLS, tg, self.get_image_for_file(os.path.basename(tg))))
                else:
                    c = 0
                    for tg in targets:
                        if c == OUT_COLS:
                            f.write('</tr>\n<tr>\n')
                            c = 0
                        tg = os.path.relpath(os.path.abspath(tg), start=self.out_dir)
                        f.write('<td class="out-cell"><a href="{}">{}</a></td>\n'.
                                format(tg, self.get_image_for_file(os.path.basename(tg))))
                        c = c+1
                    for _ in range(c, OUT_COLS):
                        f.write('<td class="out-cell"></td>\n')
                f.write('</tr></tbody>\n')
                f.write('</table>\n')
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
        name = os.path.basename(name)
        # Create a tree with all the outputs
        o_tree = {}
        for o in RegOutput.get_outputs():
            cat = o._category
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
        with document:
            self.options = Navigate_ResultsOptions
            """ [dict] Options for the `navigate_results` output """

    @staticmethod
    def get_conf_examples(name, layers, templates):
        outs = BaseOutput.simple_conf_examples(name, 'Web page to browse the results', 'Browse')  # noqa: F821
        outs[0]['options'] = {'link_from_root': 'index.html'}
        return outs
