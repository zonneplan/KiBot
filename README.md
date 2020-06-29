# KiPlot

![Python application](https://github.com/INTI-CMNB/kiplot/workflows/Python%20application/badge.svg) [![Coverage Status](https://coveralls.io/repos/github/INTI-CMNB/kiplot/badge.svg?branch=master&service=github)](https://coveralls.io/github/INTI-CMNB/kiplot?branch=master)

KiPlot is a program which helps you to plot your KiCad PCBs to output
formats easily, repeatable, and most of all, scriptably. This means you
can use a Makefile to export your KiCad PCBs just as needed.

For example, it's common that you might want for each board rev:

* Check ERC/DRC one last time (using [KiCad Automation Scripts](https://github.com/INTI-CMNB/kicad-automation-scripts/))
* Gerbers, drills and drill maps for a fab in their favourite format
* Fab docs for the assembler
* Pick and place files
* PCB 3D model in STEP format

You want to do this in a one-touch way, and make sure everything you need to
do so it securely saved in version control, not on the back of an old
datasheet.

KiPlot lets you do this.

As a side effect of providing a scriptable plot driver for KiCad, KiPlot also
allows functional testing of KiCad plot functions, which would otherwise be
somewhat unwieldy to write.

## The configuration file

Kiplot uses a configuration file where you can specify what *outputs* to
generate. By default you'll generate all of them, but you can specify which
ones from the command line.

The configuration file should be named **.kiplot.yaml**. The format used is
[YAML](https://yaml.org/). This is basically a text file with some structure.
This file can be compressed using *gzip* file format.

### The header

All configuration files must start with:

```
kiplot:
  version: 1
```

This tells to Kiplot that this file is using version 1 of the format.

### The *preflight* section

This section is used to specify tasks that will executed before generating any output. The available tasks are:

- `run_erc` To run the ERC (Electrical Rules Check). To ensure the schematic is electrically correct. 
- `run_drc` To run the DRC (Distance Rules Check). To ensure we have a valid PCB.
- `update_xml` To update the XML version of the BoM (Bill of Materials). To ensure our generated BoM is up to date.
- `check_zone_fills` Zones are filled before doing any operation involving PCB layers.
 
The `run_drc` command has the following option:
- `ignore_unconnected` Ignores the unconnected nets. Useful if you didn't finish the routing.

Here is an example of a *preflight* section:

```
preflight:
  run_erc: true
  update_xml: true
  run_drc: true
  check_zone_fills: true
  ignore_unconnected: false
```

### Filtering DRC/ERC errors

Sometimes KiCad reports DRC or ERC errors that you can't get rid off. This could be just because you are part of a team including lazzy people that doesn't want to take the extra effort to solve some errors that aren't in fact errors, just small violations made on purpose. In this case you could exclude some known errors.

For this you must declare `filters` entry in the `preflight` section. Then you can add as many `filter` entries as you want. Each filter entry has an optional description and defines to which error type is applied (`number`) and a regular expression that the error must match to be ignored (`regex`). Like this:

```
  filters:
    - filter: 'Optional filter description'
      number: Numeric_error_type
      regex:  'Expression to match'
```

Here is an example, suppose you are getting the following errors:

```
** Found 1 DRC errors **
ErrType(4): Track too close to pad
    @(177.185 mm, 78.315 mm): Track 1.000 mm [Net-(C3-Pad1)] on F.Cu, length: 1.591 mm
    @(177.185 mm, 80.715 mm): Pad 2 of C3 on F.Cu and others

** Found 1 unconnected pads **
ErrType(2): Unconnected items
    @(177.185 mm, 73.965 mm): Pad 2 of C4 on F.Cu and others
    @(177.185 mm, 80.715 mm): Pad 2 of C3 on F.Cu and others
```

And you want to ignore them. You can add the following filters:

```
  filters:
    - filter: 'Ignore C3 pad 2 too close to anything'
      number: 4
      regex:  'Pad 2 of C3'
    - filter: 'Ignore unconnected pad 2 of C4'
      number: 2
      regex:  'Pad 2 of C4'
```

If you need to match text from two different lines in the error message try using `(?s)TEXT(.*)TEXT_IN_OTHER_LINE`.

If you have two or more different options for a text to match try using `(OPTION1|OPTION2)`.

A complete Python regular expressions explanation is out the scope of this manual. For a complete reference consult the [Python manual](https://docs.python.org/3/library/re.html).

**Important note**: this will create a file named *kiplot_errors.filter* in the output directory.

### The *outputs* section

In this section you put all the things that you want to generate.  This section contains one or more **outputs**. Each output contain the following data:

- `name` a name so you can easily identify it.
- `comment` a short description of this output.
- `type` selects which type of output will be generated. Examples are *gerbers*, *drill files* and *pick & place files*
- `dir` is the directory where this output will be stored.
- `options` contains one or more options to configure this output.
- `layers` a list of layers used for this output. Not all outputs needs this subsection.

The available values for *type* are:
- Plot formats:
    - `gerber` the gerbers for fabrication.
    - `ps` postscript plot
    - `hpgl` format for laser printers
    - `svg` scalable vector graphics
    - `pdf` portable document format
    - `dxf` mechanical CAD format
- Drill formats:
    - `excellon` data for the drilling machine
    - `gerb_drill` drilling positions in a gerber file
- Pick & place
    - `position` of the components for the pick & place machine
- Documentation
    - `pdf_sch_print` schematic in PDF format
    - `pdf_pcb_print`PDF file containing one or more layer and the page frame
- Bill of Materials
    - `kibom` BoM in HTML or CSV format generated by [KiBoM](https://github.com/INTI-CMNB/KiBoM)
    - `ibom` Interactive HTML BoM generated by [InteractiveHtmlBom](https://github.com/INTI-CMNB/InteractiveHtmlBom)
- 3D model:
    - `step` *Standard for the Exchange of Product Data* for the PCB

Here is an example of a configuration file to generate the gerbers for the top and bottom layers:

```
kiplot:
  version: 1

preflight:
  run_drc: true

outputs:

  - name: 'gerbers'
    comment: "Gerbers for the board house"
    type: gerber
    dir: gerberdir
    options:
      # generic layer options
      exclude_edge_layer: false
      exclude_pads_from_silkscreen: false
      plot_sheet_reference: false
      plot_footprint_refs: true
      plot_footprint_values: true
      force_plot_invisible_refs_vals: false
      tent_vias: true
      line_width: 0.15

      # gerber options
      use_aux_axis_as_origin: false
      subtract_mask_from_silk: true
      use_protel_extensions: false
      gerber_precision: 4.5
      create_gerber_job_file: true
      use_gerber_x2_attributes: true
      use_gerber_net_attributes: false

    layers:
      - layer: F.Cu
        suffix: F_Cu
      - layer: B.Cu
        suffix: B_Cu
```

Most options are the same you'll find in the KiCad dialogs.

### Supported outputs:

* DXF (Drawing Exchange Format)
  * Type: `dxf`
  * Description: Exports the PCB to 2D mechanical EDA tools (like AutoCAD).
                 This output is what you get from the File/Plot menu in pcbnew.
  * Options:
    - `drill_marks`: [string='full'] drill_marks what to use to indicate the drill places, can be none, small or full (for real scale).
    - `exclude_edge_layer`: [boolean=true] do not include the PCB edge layer.
    - `exclude_pads_from_silkscreen`: [boolean=false] do not plot the component pads in the silk screen.
    - `force_plot_invisible_refs_vals`: [boolean=false] include references and values even when they are marked as invisible.
    - `plot_footprint_refs`: [boolean=true] include the footprint references.
    - `plot_footprint_values`: [boolean=true] include the footprint values.
    - `plot_sheet_reference`: [boolean=false] currently without effect.
    - `polygon_mode`: [boolean=true] plot using the contour, instead of the center line.
    - `sketch_plot`: [boolean=false] don't fill objects, just draw the outline.
    - `tent_vias`: [boolean=true] cover the vias.
    - `use_aux_axis_as_origin`: [boolean=false] use the auxiliar axis as origin for coordinates.

* Excellon drill format
  * Type: `excellon`
  * Description: This is the main format for the drilling machine.
                 You can create a map file for documentation purposes.
                 This output is what you get from the 'File/Fabrication output/Drill Files' menu in pcbnew.
  * Options:
    - `map`:  [string=None] format for a graphical drill map. The valid formats are hpgl, ps, gerber, dxf, svg and pdf.
                Not generated unless a format is specified.
    - `metric_units`: [boolean=true] use metric units instead of inches.
    - `minimal_header`: [boolean=false] use a minimal header in the file.
    - `mirror_y_axis`: [boolean=false] invert the Y axis.
    - `pth_and_npth_single_file`: [boolean=true] generate one file for both, plated holes and non-plated holes, instead of two separated files.
    - `report`:  [string=None] name of the drill report. Not generated unless a name is specified.
    - `use_aux_axis_as_origin`: [boolean=false] use the auxiliar axis as origin for coordinates.

* Gerber drill format
  * Type: `gerb_drill`
  * Description: This is the information for the drilling machine in gerber format.
                 You can create a map file for documentation purposes.
                 This output is what you get from the 'File/Fabrication output/Drill Files' menu in pcbnew.
  * Options:
    - `map`:  [string=None] format for a graphical drill map. The valid formats are hpgl, ps, gerber, dxf, svg and pdf.
                Not generated unless a format is specified.
    - `report`:  [string=None] name of the drill report. Not generated unless a name is specified.
    - `use_aux_axis_as_origin`: [boolean=false] use the auxiliar axis as origin for coordinates.

* Gerber format
  * Type: `gerber`
  * Description: This is the main fabrication format for the PCB.
                 This output is what you get from the File/Plot menu in pcbnew.
  * Options:
    - `create_gerber_job_file`: [boolean=true] creates a file with information about all the generated gerbers.
                You can use it in gerbview to load all gerbers at once.
    - `exclude_edge_layer`: [boolean=true] do not include the PCB edge layer.
    - `exclude_pads_from_silkscreen`: [boolean=false] do not plot the component pads in the silk screen.
    - `force_plot_invisible_refs_vals`: [boolean=false] include references and values even when they are marked as invisible.
    - `gerber_precision`: [number=4.6] this the gerber coordinate format, can be 4.5 or 4.6.
    - `line_width`: [number=0.1] line_width for objects without width [mm].
    - `plot_footprint_refs`: [boolean=true] include the footprint references.
    - `plot_footprint_values`: [boolean=true] include the footprint values.
    - `plot_sheet_reference`: [boolean=false] currently without effect.
    - `subtract_mask_from_silk`: [boolean=false] substract the solder mask from the silk screen.
    - `tent_vias`: [boolean=true] cover the vias.
    - `use_aux_axis_as_origin`: [boolean=false] use the auxiliar axis as origin for coordinates.
    - `use_gerber_net_attributes`: [boolean=true] include netlist metadata.
    - `use_gerber_x2_attributes`: [boolean=true] use the extended X2 format.
    - `use_protel_extensions`: [boolean=false] use legacy Protel file extensions.

* HPGL (Hewlett & Packard Graphics Language)
  * Type: `hpgl`
  * Description: Exports the PCB for plotters and laser printers.
                 This output is what you get from the File/Plot menu in pcbnew.
  * Options:
    - `drill_marks`: [string='full'] what to use to indicate the drill places, can be none, small or full (for real scale).
    - `exclude_edge_layer`: [boolean=true] do not include the PCB edge layer.
    - `exclude_pads_from_silkscreen`: [boolean=false] do not plot the component pads in the silk screen.
    - `force_plot_invisible_refs_vals`: [boolean=false] include references and values even when they are marked as invisible.
    - `mirror_plot`: [boolean=false] plot mirrored.
    - `pen_width`: [number=0.5] pen diameter in MILS, useful to fill areas. However, it is in mm in HPGL files.
    - `plot_footprint_refs`: [boolean=true] include the footprint references.
    - `plot_footprint_values`: [boolean=true] include the footprint values.
    - `plot_sheet_reference`: [boolean=false] currently without effect.
    - `scaling`: [number=0] scale factor (0 means autoscaling).
    - `sketch_plot`: [boolean=false] don't fill objects, just draw the outline.
    - `tent_vias`: [boolean=true] cover the vias.

* IBoM (Interactive HTML BoM)
  * Type: `ibom`
  * Description: Generates an interactive web page useful to identify the position of the components in the PCB.
                 For more information: https://github.com/INTI-CMNB/InteractiveHtmlBom
                 This output is what you get from the InteractiveHtmlBom plug-in (pcbnew).
  * Options:
    - `blacklist`: [string=''] List of comma separated blacklisted components or prefixes with *. E.g. 'X1,MH*'.
    - `blacklist_empty_val`: [boolean=false] Blacklist components with empty value.
    - `board_rotation`: [number=0] Board rotation in degrees (-180 to 180). Will be rounded to multiple of 5.
    - `bom_view`: [string='left-right'] Default BOM view {bom-only,left-right,top-bottom}.
    - `checkboxes`: [string='Sourced,Placed'] Comma separated list of checkbox columns.
    - `dark_mode`: [boolean=false] Default to dark mode.
    - `dnp_field`: [string=''] Name of the extra field that indicates do not populate status. Components with this field not empty will be
                blacklisted.
    - `extra_fields`: [string=''] Comma separated list of extra fields to pull from netlist or xml file.
    - `hide_pads`: [boolean=false] Hide footprint pads by default.
    - `hide_silkscreen`: [boolean=false] Hide silkscreen by default.
    - `highlight_pin1`: [boolean=false] Highlight pin1 by default.
    - `include_nets`: [boolean=false] Include netlist information in output..
    - `include_tracks`: [boolean=false] Include track/zone information in output. F.Cu and B.Cu layers only.
    - `layer_view`: [string='FB'] Default layer view {F,FB,B}.
    - `name_format`: [string='ibom'] Output file name format supports substitutions:
                %f : original pcb file name without extension.
                %p : pcb/project title from pcb metadata.
                %c : company from pcb metadata.
                %r : revision from pcb metadata.
                %d : pcb date from metadata if available, file modification date otherwise.
                %D : bom generation date.
                %T : bom generation time. Extension .html will be added automatically.
    - `netlist_file`: [string=''] Path to netlist or xml file.
    - `no_blacklist_virtual`: [boolean=false] Do not blacklist virtual components.
    - `no_redraw_on_drag`: [boolean=false] Do not redraw pcb on drag by default.
    - `normalize_field_case`: [boolean=false] Normalize extra field name case. E.g. 'MPN' and 'mpn' will be considered the same field.
    - `show_fabrication`: [boolean=false] Show fabrication layer by default.
    - `sort_order`: [string='C,R,L,D,U,Y,X,F,SW,A,~,HS,CNN,J,P,NT,MH'] Default sort order for components. Must contain '~' once.
    - `variant_field`: [string=''] Name of the extra field that stores board variant for component.
    - `variants_blacklist`: [string=''] List of board variants to exclude from the BOM.
    - `variants_whitelist`: [string=''] List of board variants to include in the BOM.

* KiBoM (KiCad Bill of Materials)
  * Type: `kibom`
  * Description: Used to generate the BoM in HTML or CSV format using the KiBoM plug-in.
                 For more information: https://github.com/INTI-CMNB/KiBoM
                 This output is what you get from the 'Tools/Generate Bill of Materials' menu in eeschema.
  * Options:
    - `format`: [string='HTML'] can be `HTML` or `CSV`.

* PDF (Portable Document Format)
  * Type: `pdf`
  * Description: Exports the PCB to the most common exhange format. Suitable for printing.
                 Note that this output isn't the best for documating your project.
                 This output is what you get from the File/Plot menu in pcbnew.
  * Options:
    - `drill_marks`: [string='full'] what to use to indicate the drill places, can be none, small or full (for real scale).
    - `exclude_edge_layer`: [boolean=true] do not include the PCB edge layer.
    - `exclude_pads_from_silkscreen`: [boolean=false] do not plot the component pads in the silk screen.
    - `force_plot_invisible_refs_vals`: [boolean=false] include references and values even when they are marked as invisible.
    - `line_width`: [number=0.1] for objects without width [mm].
    - `mirror_plot`: [boolean=false] plot mirrored.
    - `negative_plot`: [boolean=false] invert black and white.
    - `plot_footprint_refs`: [boolean=true] include the footprint references.
    - `plot_footprint_values`: [boolean=true] include the footprint values.
    - `plot_sheet_reference`: [boolean=false] currently without effect.
    - `tent_vias`: [boolean=true] cover the vias.

* PDF PCB Print (Portable Document Format)
  * Type: `pdf_pcb_print`
  * Description: Exports the PCB to the most common exhange format. Suitable for printing.
                 This is the main format to document your PCB.
                 This output is what you get from the 'File/Print' menu in pcbnew.
  * Options:
    - `output_name`: [string=''] filename for the output PDF (the name of the PCB if empty).

* PDF Schematic Print (Portable Document Format)
  * Type: `pdf_sch_print`
  * Description: Exports the PCB to the most common exhange format. Suitable for printing.
                 This is the main format to document your schematic.
                 This output is what you get from the 'File/Print' menu in eeschema.
  * Options:
    - `output`: [string=''] filename for the output PDF (the name of the schematic if empty).

* Pick & place
  * Type: `position`
  * Description: Generates the file with position information for the PCB components, used by the pick and place machine.
                 This output is what you get from the 'File/Fabrication output/Footprint poistion (.pos) file' menu in pcbnew.
  * Options:
    - `format`: [string='ASCII'] can be ASCII or CSV.
    - `only_smd`: [boolean=true] only include the surface mount components.
    - `separate_files_for_front_and_back`: [boolean=true] generate two separated files, one for the top and another for the bottom.
    - `units`: [string='millimeters'] can be millimeters or inches.

* PS (Postscript)
  * Type: `ps`
  * Description: Exports the PCB to a format suitable for printing.
                 This output is what you get from the File/Plot menu in pcbnew.
  * Options:
    - `a4_output`: [boolean=true] force A4 paper size.
    - `drill_marks`: [string='full'] what to use to indicate the drill places, can be none, small or full (for real scale).
    - `exclude_edge_layer`: [boolean=true] do not include the PCB edge layer.
    - `exclude_pads_from_silkscreen`: [boolean=false] do not plot the component pads in the silk screen.
    - `force_plot_invisible_refs_vals`: [boolean=false] include references and values even when they are marked as invisible.
    - `line_width`: [number=0.15] for objects without width [mm].
    - `mirror_plot`: [boolean=false] plot mirrored.
    - `negative_plot`: [boolean=false] invert black and white.
    - `plot_footprint_refs`: [boolean=true] include the footprint references.
    - `plot_footprint_values`: [boolean=true] include the footprint values.
    - `plot_sheet_reference`: [boolean=false] currently without effect.
    - `scale_adjust_x`: [number=1.0] fine grain adjust for the X scale (floating point multiplier).
    - `scale_adjust_y`: [number=1.0] fine grain adjust for the Y scale (floating point multiplier).
    - `scaling`: [number=1] scale factor (0 means autoscaling).
    - `sketch_plot`: [boolean=false] don't fill objects, just draw the outline.
    - `tent_vias`: [boolean=true] cover the vias.
    - `width_adjust`: [number=0] this width factor is intended to compensate PS printers/plotters that do not strictly obey line width settings.
                Only used to plot pads and tracks.

* STEP (ISO 10303-21 Clear Text Encoding of the Exchange Structure)
  * Type: `step`
  * Description: Exports the PCB as a 3D model.
                 This is the most common 3D format for exchange purposes.
                 This output is what you get from the 'File/Export/STEP' menu in pcbnew.
  * Options:
    - `metric_units`: [boolean=true] use metric units instead of inches..
    - `min_distance`: [number=-1] the minimum distance between points to treat them as separate ones (-1 is KiCad default: 0.01 mm).
    - `no_virtual`: [boolean=false] used to exclude 3D models for components with 'virtual' attribute.
    - `origin`: [string='grid'] determines the coordinates origin. Using grid the coordinates are the same as you have in the design sheet.
                The drill option uses the auxiliar reference defined by the user.
                You can define any other origin using the format 'X,Y', i.e. '3.2,-10'.
    - `output`: [string=''] name for the generated STEP file (the name of the PCB if empty).

* SVG (Scalable Vector Graphics)
  * Type: `svg`
  * Description: Exports the PCB to a format suitable for 2D graphics software.
                 Unlike bitmaps SVG drawings can be scaled without losing resolution.
                 This output is what you get from the File/Plot menu in pcbnew.
  * Options:
    - `drill_marks`: [string='full'] what to use to indicate the drill places, can be none, small or full (for real scale).
    - `exclude_edge_layer`: [boolean=true] do not include the PCB edge layer.
    - `exclude_pads_from_silkscreen`: [boolean=false] do not plot the component pads in the silk screen.
    - `force_plot_invisible_refs_vals`: [boolean=false] include references and values even when they are marked as invisible.
    - `line_width`: [number=0.25] for objects without width [mm].
    - `mirror_plot`: [boolean=false] plot mirrored.
    - `negative_plot`: [boolean=false] invert black and white.
    - `plot_footprint_refs`: [boolean=true] include the footprint references.
    - `plot_footprint_values`: [boolean=true] include the footprint values.
    - `plot_sheet_reference`: [boolean=false] currently without effect.
    - `tent_vias`: [boolean=true] cover the vias.


## Using KiPlot

If the current directory contains only one PCB file and only one configuration file (named *.kiplot.yaml)
you can just call `kiplot`. No arguments needed. The tool will figure out which files to use.

If more than one file is found in the current directory `kiplot` will use the first found and issue a
warning. If you need to use other file just tell it explicitly:

```
kiplot -b PCB_FILE.kicad_pcb -c CONFIG.kiplot.yaml
```

A simple target can be added to your `makefile`, so you can just run
`make pcb_files` or integrate into your current build process.

```
pcb_files:
    kiplot -b $(PCB) -c $(KIPLOT_CFG)
```

If you need to supress messages use `--quiet` or `-q` and if you need to get more informatio about
what's going on use `--verbose` or `-v`.

If you want to generate only some of the outputs use:

```
kiplot OUTPUT_1 OUTPUT_2
```

If you want to generate all outputs with some exceptions use:


```
kiplot --invert-sel OUTPUT_1 OUTPUT_2
```

If you want to skip the DRC and ERC use:

```
kiplot --skip-pre run_erc,run_drc
```

If you want to skip all the `preflight` tasks use:

```
kiplot --skip-pre all
```

All outputs are generated using the current directory as base. If you want to use another
directory as base use:

```
kiplot --out-dir OTHER_PLACE
```

If you want to list the available outputs defined in the configuration file use:

```
kiplot --list
```

### Command line help

```
KiPlot: Command-line Plotting for KiCad

Usage:
  kiplot [-b BOARD] [-e SCHEMA] [-c CONFIG] [-d OUT_DIR] [-s PRE]
         [-q | -v...] [-i] [TARGET...]
  kiplot [-c PLOT_CONFIG] --list
  kiplot --help-list-outputs
  kiplot --help-output=HELP_OUTPUT
  kiplot --help-outputs
  kiplot --help-preflights
  kiplot -h | --help
  kiplot --version

Arguments:
  TARGET    Outputs to generate, default is all

Options:
  -h, --help                       Show this help message and exit
  -b BOARD, --board-file BOARD     The PCB .kicad-pcb board file
  -c CONFIG, --plot-config CONFIG  The plotting config file to use
  -d OUT_DIR, --out-dir OUT_DIR    The output directory [default: .]
  -e SCHEMA, --schematic SCHEMA    The schematic file (.sch)
  --help-list-outputs              List supported outputs
  --help-output HELP_OUTPUT        Help for this particular output
  --help-outputs                   List supported outputs and details
  --help-preflights                List supported preflights and details
  -i, --invert-sel                 Generate the outputs not listed as targets
  -l, --list                       List available outputs (in the config file)
  -q, --quiet                      Remove information logs
  -s PRE, --skip-pre PRE           Skip preflights, comma separated or `all`
  -v, --verbose                    Show debugging information
  --version, -V                    Show program's version number and exit

```

## Installing

### Dependencies

- For ERC, DRC, BoM XML update and PCB/SCH print install [KiCad Automation Scripts](https://github.com/INTI-CMNB/kicad-automation-scripts/)
- For HTML/CSV BoM install [KiBoM](https://github.com/INTI-CMNB/KiBoM)
- For interactive BoM install [InteractiveHtmlBom](https://github.com/INTI-CMNB/InteractiveHtmlBom)

### Installation on Ubuntu/Debian:

Get the Debian package from the [releases section](https://github.com/INTI-CMNB/kiplot/releases) and run:
```
sudo apt install ./kiplot.inti-cmnb_*_all.deb
```

### Installation on other targets

- Install KiCad 5.x
- Install Python 3.5 or newer
- Install the Python Yaml module
- Run the script *src/kiplot*


## Using for CI/CD

When using a GitHub or GitLab repo you can use KiPlot to generate all the needed stuff each time you commit a change to the schematic and/or PCB file.

Examples of how to do it can be found [here for GitHub](https://github.com/INTI-CMNB/kicad_ci_test) and [here for GitLab](https://gitlab.com/set-soft/kicad-ci-test).

In order to run KiPlot on these environments you need a lot of software installed. The usual mechanism to achieve this is using [docker](https://www.docker.com/). Docker images containing KiPlot, all the supporting scripts and a corresponding KiCad can be found at [Docker Hub](https://hub.docker.com/) as [setsoft/kicad_auto:latest](https://hub.docker.com/repository/docker/setsoft/kicad_auto). This image is based on [setsoft/kicad_debian:latest](https://hub.docker.com/repository/docker/setsoft/kicad_debian), containing KiCad on Debian GNU/Linux.

For more information about the docker images visit [kicad_debian](https://github.com/INTI-CMNB/kicad_debian) and [kicad_auto](https://github.com/INTI-CMNB/kicad_auto).

