# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# The Assembly image is a composition from Pixlok and oNline Web Fonts
# The rest are KiCad icons
import os
from shutil import copy2
from math import ceil
from .gs import GS
import pprint
from .optionable import BaseOptions
from .kiplot import config_output, get_output_dir
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log, __version__

logger = log.get_logger()
CAT_IMAGE = {'PCB': 'pcbnew.svg',
             'Schematic': 'eeschema.svg',
             'fabrication': 'fabrication.svg',
             'export': 'export.svg',
             'assembly': 'assembly_simple.svg',
             'repair': 'repair.svg',
             'docs': 'project.svg',
             'BoM': 'bom.svg',
             '3D': '3d.svg',
             'gerber': 'gerber.svg',
             'drill': 'load_drill.svg'}
EXT_IMAGE = {'gbr': 'file_gbr.svg',
             'gtl': 'file_gbr.svg',
             'gtp': 'file_gbr.svg',
             'gbo': 'file_gbr.svg',
             'gto': 'file_gbr.svg',
             'gbs': 'file_gbr.svg',
             'gbl': 'file_gbr.svg',
             'gts': 'file_gbr.svg',
             'gml': 'file_gbr.svg',
             'gm1': 'file_gbr.svg',
             'gbrjob': 'file_gerber_job.svg',
             'brd': 'file_brd.svg',
             'dxf': 'file_dxf.svg',
             'cad': 'file_cad.svg',
             'drl': 'file_drl.svg',
             'pdf': 'file_pdf.svg',
             'txt': 'file_txt.svg',
             'pos': 'file_pos.svg',
             'csv': 'file_csv.svg',
             'svg': 'file_svg.svg',
             'eps': 'file_eps.svg',
             'png': 'file_png.svg',
             'jpg': 'file_jpg.svg',
             'plt': 'file_plt.svg',
             'ps': 'file_ps.svg',
             'step': 'file_stp.svg',
             'stp': 'file_stp.svg',
             'html': 'file_html.svg',
             'xml': 'file_xml.svg',
             'tsv': 'file_tsv.svg',
             'xlsx': 'file_xlsx.svg',
             'xyrs': 'file_xyrs.svg'}
for i in range(31):
    n = str(i)
    EXT_IMAGE['gl'+n] = 'file_gbr.svg'
    EXT_IMAGE['g'+n] = 'file_gbr.svg'
    EXT_IMAGE['gp'+n] = 'file_gbr.svg'
BIG_ICON = 256
MID_ICON = 64
OUT_COLS = 10

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

    def copy(self, img):
        copy2(os.path.join(self.img_src_dir, img), os.path.join(self.out_dir, img))

    def get_image_for_cat(self, cat):
        if cat in CAT_IMAGE:
            img = 'images/'+CAT_IMAGE[cat]
            cat_img = '<img src="{}" alt="{}" width="{}" height="{}">'.format(img, cat, BIG_ICON, BIG_ICON)
            cat = ('<table class="cat-img"><tr><td>{}<br>{}</td></tr></table>'.
                   format(cat_img, cat))
            self.copy(img)
        return cat

    def get_image_for_file(self, file):
        ext = os.path.splitext(file)[1][1:].lower()
        img = 'images/'+EXT_IMAGE.get(ext, 'unknown.svg')
        ext_img = '<img src="{}" alt="{}" width="{}" height="{}">'.format(img, file, MID_ICON, MID_ICON)
        file = ('<table class="out-img"><tr><td>{}</td></tr><tr><td class="td-small">{}</td></tr></table>'.
                format(ext_img, file))
        self.copy(img)
        return file

    def add_back_home(self, f, prev):
        if prev is not None:
            prev += '.html'
            f.write('<table class="nav-table">')
            f.write(' <tr>')
            f.write('  <td><a href="{}"><img src="images/back.svg" width="{}" height="{}" alt="go back"></a></td>'.
                    format(prev, MID_ICON, MID_ICON))
            f.write('  <td><a href="{}"><img src="images/home.svg" width="{}" height="{}" alt="go home"></a></td>'.
                    format(self.home, MID_ICON, MID_ICON))
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
                c = 0
                for tg in out.get_targets(out_dir):
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
        # Create the pages
        self.home = name
        self.copy('images/back.svg')
        self.copy('images/home.svg')
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
