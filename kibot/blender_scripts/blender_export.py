# -*- coding: utf-8 -*-
# Copyright (c) 2023 Salvador E. Tropea
# Copyright (c) 2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Based on:
# - background_job.py: Blender example
#   https://developer.blender.org/diffusion/B/browse/master/release/scripts/templates_py/background_job.py
# - blender_pcb2gltf.py: PCB3D to various formats
#   https://github.com/Haschtl/pcb2blender/blob/master/CI/blender_pcb2gltf.py
#
# Should be invoked using:
# blender -b --factory-startup -P blender_export.py -- OPTIONS
import addon_utils
import bpy


VALID_FORMATS = {'fbx': 'Filmbox, proprietary format developed by Kaydara (owned by Autodesk)',
                 'obj': 'geometry definition format developed by Wavefront Technologies. Currently open',
                 'x3d': 'VRML successor. A royalty-free ISO/IEC standard for declaratively representing 3D graphics.',
                 'blender': 'Blender native format',
                 'gltf': 'standard file format for three-dimensional scenes and models.',
                 'stl': '3D printing from stereolithography CAD software created by 3D SystemsSTL (only mesh)',
                 'ply': 'Polygon File Format or the Stanford Triangle Format (only mesh)'}


def fbx_export(name):
    bpy.ops.export_scene.fbx(filepath=name)


def obj_export(name):
    bpy.ops.export_scene.obj(filepath=name)


def x3d_export(name):
    bpy.ops.export_scene.x3d(filepath=name)


def stl_export(name):
    bpy.ops.export_mesh.stl(filepath=name)


def ply_export(name):
    bpy.ops.export_mesh.ply(filepath=name)


def blender_export(name):
    bpy.ops.wm.save_as_mainfile(filepath=name)


def gltf_export(name):
    bpy.ops.export_scene.gltf(filepath=name, export_copyright="KiBot", export_draco_mesh_compression_enable=True,
                              export_draco_mesh_compression_level=6, export_colors=False, export_yup=True)


EXPORTERS = {'fbx': fbx_export,
             'obj': obj_export,
             'x3d': x3d_export,
             'stl': stl_export,
             'ply': ply_export,
             'blender': blender_export,
             'gltf': gltf_export}


def main():
    import argparse  # to parse options for us and print a nice help message
    import os
    import sys       # to get command line args
    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv
    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--")+1:]  # get all args after "--"

    description = ("Blender script to export PCB3D files into various formats.\n"
                   "The pcb2blender_importer plug-in must be installed.\n"
                   "Consult: https://github.com/30350n/pcb2blender")
    prog = "blender -b --factory-startup -P blender_export.py --"
    epilog = "Valid formats:\n"
    for f, desc in VALID_FORMATS.items():
        epilog += f"{f}: {desc}\n"

    parser = argparse.ArgumentParser(description=description, prog=prog, epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-c", "--no_components", action="store_false", help="if the PCB components are discarded")
    parser.add_argument("-C", "--dont_cut_boards", action="store_false", help="do not separate sub-PCBs")
    parser.add_argument("-d", "--texture_dpi", type=float, help="textures density [508-2032] [1016]", default=1016.0)
    parser.add_argument("-D", "--dont_center", action="store_false", help="do not center the PCB at 0,0")
    parser.add_argument("-E", "--dont_enhance_materials", action="store_false", help="do not enhance materials")
    parser.add_argument("-f", "--format", type=str, required=True, nargs='+', choices=VALID_FORMATS.keys(),
                        help="output formats to export, can be repeated")
    parser.add_argument("-m", "--pcb_material", type=str, choices=["RASTERIZED", "3D"], default="RASTERIZED",
                        help="Rasterized (Cycles) or 3D (deprecated) [RASTERIZED]")
    parser.add_argument("-M", "--dont_merge_materials", action="store_false", help="do not merge materials")
    parser.add_argument("-o", "--output", type=str, required=True, nargs='+', help="output file name, can be repeated")
    parser.add_argument("-s", "--solder_joints", type=str, choices=["NONE", "SMART", "ALL"], default="SMART",
                        help="Add none, all or only for THT/SMD with solder paste [SMART]")
    parser.add_argument("-S", "--dont_stack_boards", action="store_false", help="do not stack sub-PCBs")

    parser.add_argument('PCB3D_file')
    args = parser.parse_args(argv)

    nformats = len(args.format)
    if nformats != len(args.output):
        print("Please use -f and -o the same amount of times")
        sys.exit(2)

    print("Importing PCB3D file ...")
    PCB3D_file = os.path.abspath(args.PCB3D_file)
    # Start with fresh settings
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Now enable the plug-in
    addon_utils.enable("pcb2blender_importer")
    # Import the PCB3D file
    bpy.ops.pcb2blender.import_pcb3d(filepath=PCB3D_file, pcb_material=args.pcb_material,
                                     import_components=args.no_components,
                                     add_solder_joints=args.solder_joints,
                                     center_pcb=args.dont_center,
                                     merge_materials=args.dont_merge_materials,
                                     enhance_materials=args.dont_enhance_materials,
                                     cut_boards=args.dont_cut_boards,
                                     stack_boards=args.dont_stack_boards,
                                     texture_dpi=args.texture_dpi)
    # Do all the exports
    for f, o in zip(args.format, args.output):
        print(f"Exporting {o} in {f} format")
        EXPORTERS[f](os.path.abspath(o))

    print("batch job finished, exiting")


if __name__ == "__main__":
    main()
