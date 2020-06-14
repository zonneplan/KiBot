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
 
The `run_drc` command has the following options:
- `check_zone_fills` Every time we run the DRC the zones are filled again. This option saves the PCB to disk updating the zones.
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
      check_zone_fills: true
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

### General options for plot formats

- `exclude_edge_layer` do not include the PCB edge layer
- `exclude_pads_from_silkscreen` do not plot the component pads in the silk screen
- `plot_sheet_reference` currently without effect
- `plot_footprint_refs` include the footprint references
- `plot_footprint_values` include the footprint values
- `force_plot_invisible_refs_vals` include references and values even when they are marked as invisible
- `tent_vias` cover the vias
- `check_zone_fills` currently without effect

Note that each layer is generated in a separated file.

### Gerber options

- `line_width` for objects without width (floating point value in mm)
- `use_aux_axis_as_origin` use the auxiliar axis as origin for coordinates
- `subtract_mask_from_silk` substract the solder mask from the silk screen
- `use_protel_extensions` use legacy Protel file extensions
- `gerber_precision` this the gerber coordinate format, can be 4.5 or 4.6
- `create_gerber_job_file` creates a file with information about all the generated gerbers. You can use it in *gerbview* to load all gerbers at once.
- `use_gerber_x2_attributes` use the extended X2 format
- `use_gerber_net_attributes` include netlist metadata

### PS options

- `line_width` for objects without width (floating point value in mm)
- `mirror_plot` plot mirrored
- `negative_plot` invert black and white
- `scaling` scale factor
- `drill_marks` what to use to indicate the drill places, can be `none`, `small` or `full` (for real scale)
- `scale_adjust_x` fine grain adjust for the X scale (floating point multiplier)
- `scale_adjust_y` fine grain adjust for the Y scale (floating point multiplier)
- `a4_output` force A4 paper size

### SVG and PDF options

- `line_width` for objects without width (floating point value in mm)
- `mirror_plot` plot mirrored
- `negative_plot` invert black and white
- `drill_marks` what to use to indicate the drill places, can be `none`, `small` or `full` (for real scale)

### HPGL options

- `mirror_plot` plot mirrored
- `scaling` scale factor
- `drill_marks` what to use to indicate the drill places, can be `none`, `small` or `full` (for real scale)
- `pen_width` default trace width

### DXF options

- `drill_marks` what to use to indicate the drill places, can be `none`, `small` or `full` (for real scale)
- `polygon_mode` plot using the contour, instead of the center line

### General drill options

- `use_aux_axis_as_origin` use the auxiliar axis as origin for coordinates
- `map` this is an optional subsection to indicate the format for a graphical drill map.
The valid formats are `hpgl`, `ps`, `gerber`, `dxf`, `svg` and `pdf`. Example:
```
      map:
        type: 'pdf'
```
- `report` this is an optional subsection to indicate the name of the drill report, example:
```
      report:
        filename: 'Project-drl.rpt'
```

### Excellon drill options

- `metric_units` use metric units instead of inches.
- `pth_and_npth_single_file` generate one file for both, plated holes and non-plated holes, instead of two separated files.
- `minimal_header` use a minimal header in the file
- `mirror_y_axis` invert the Y axis

### Position options

- `format` can be `ascii` or `csv`.
- `units` can be `millimeters` or `inches`.
- `separate_files_for_front_and_back` generate two separated files, one for the top and another for the bottom.
- `only_smd` only include the surface mount components.

### pdf_pcb_print options

- `output_name` filename for the output PDF

### KiBoM options

- `format` can be `html` or `csv`.

### IBoM options

- `blacklist` regular expression for the components to exclude (using the Config field)
- `name_format` format of the output name, example: `%f_%r_iBoM` will generate a file with revision and *_iBoM*.

### pdf_sch_print options

- `output` filename for the output PDF


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

