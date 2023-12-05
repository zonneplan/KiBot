# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.6.4] - UNRELEASED
### Added
- General:
  - Operations that copies the project now also copies the PRL
- Command line:
  - `--help-list-offsets` to list footprint offsets (JLCPCB)
  - `--help-list-rotations` to list footprint rotations (JLCPCB)
- Global options:
  - `remove_solder_mask_for_dnp` similar to `remove_solder_paste_for_dnp` but
    applied to the solder mask apertures. (#476)
  - `layer_defaults` to specify the default suffix and description. (#504)
  - `include_components_from_pcb` to disable the new behavior that includes
    components from the PCB in the filter/variants processing
  - `restore_project` now also restores the PRL
- Schematic format:
  - Support for *unit names* (#513)
- Internal templates:
  - 3DRender_top, 3DRender_top_straight, 3DRender_bottom and
    3DRender_bottom_straight: to generate simple and quick 3D renders.
  - _KIBOT_POS_DNF_FILTER option to JLCPCB. It now excludes components added
    by KiKit to create panels and can be customized.
  - _KIBOT_PLOT_FOOTPRINT_REFS and  _KIBOT_PLOT_FOOTPRINT_VALUES to
    manufacturer templates. (#523)
- Filters:
  - New `_rot_footprint_jlcpcb` internal filter to fix the JLCPCB bottom
    rotations.
  - New options for the `rot_footprint` filters: (See #510)
    - `mirror_bottom`: used to undo the KiCad mirroring of the bottom.
    - `rot_fields`: list of fields to indicate arbitrary rotations.
    - `offset_fields`: list of fields to indicate arbitrary offsets.
    - `offsets`: a list of pairs containing regex and offset ("x, y")
    - `bennymeg_mode`: used to provide compatibility with the
      bennymeg/JLC-Plugin-for-KiCad tool.
    - `rotations_and_offsets`: a more flexible mechanism to select
      rotations and offsets. So you can have two different rotations
      applied to the same footprint, i.e. different components with
      the same footprint but different orientation in the reel.
- 3D outputs:
  - `download_lcsc` option to disable LCSC 3D model download (See #415)
- BoM:
  - Support for ${field} expansion. (#471)
  - LCSC links (SchrodingersGat/KiBoM#190)
  - `parse_value` can be used to disable the *Value* parser (See #494)
    Also added a warning about using extra data in the *Value* field.
- iBoM:
  - `forced_name` option to force the name displayed at the top left corner
    (#470)
- Blender export:
  - Support for pcb2blender v2.6/2.7 (Blender 3.5.1/3.6)
  - `auto_camera_z_axis_factor`: used to control the default camera distance
  - Options to create simple animations:
    - PoV `steps`: to create rotation angle increments
    - `default_file_id`: can be used to create numbered PNGs
    - `fixed_auto_camera`: to avoid adjusting the automatic camera on each frame
  - Camera option to set the clip start (#484)
  - Traceback dump when Blender output contains it
- KiKit
  - Expand text variables and KiBot %X markers in text objects (see #497)
- PCB Print:
  - Support for CURRENT_DATE text variable
- Populate:
  - Basic support for regular list items (#480)
- Position:
  - Experimental support for gerber position files (#500)
- Copy Files:
  - Mode to export the whole project (SCH, PCB, symbols, footprints, 3D models
    and project files) (#491)
- Help for the error levels
- Warnings:
  - Explain about wrong dir/output separation (#493)

### Changed
- Documentation:
  - Now you can search in the docs
  - Indexed so you can search by topic
  - With a navigation side bar
- Variants and filters:
  - Components only in the PCB are now processed
- QR Lib:
  - Footprints: now they are flagged with exclude from BoM and Pos, also
    with no court yard requirements for KiCad 7
  - Symbol: Excluded from simulation for KiCad 7

### Fixed
- Schematics: problems with deep nested and recycled sheets (#520)
- Rotated polygons and text used in the worksheet (#466)
- The --log/-L didn't enabled full debug for all messages
- BoM:
  - Problems when trying to aggregate the datasheet field (#472)
- kibot-check:
  - Show 7.x as supported (#469)
- Blender export:
  - Rotations are now applied to the current view, not just the top view
  - Board/components not visible for small boards (See #484)
  - Light type names (extra space) (#505)
- update_xml with check_pcb_parity enabled:
  - Avoid errors for KiCad 6 using "Exclude from BoM" components.
    This limitation isn't found on KiCad 7. (#486)
  - *exclude_from_bom* mismatch on KiCad 7
  - *Sheetfile* mismatch on KiCad 7 when testing from different directory
- Dependencies downloader:
  - Problems when connection timed-out
- Sub PCB separation using annotation method for some edeges and KiCad
  versions (#496)
- Problems when using NET_NAME(n) for a value (#511)
- JLCPCB rotations for bottom components
- Copy Files:
  - Warnings when using both, the STEP and WRL model, of the same component
  - Fail to detect 3D models subdirs when running alone
- QR Lib:
  - When used from the preflight the name of the file changed to the name of a
    temporal, generating problems with the plot outputs, like pcb_print
  - Project options not preserved, i.e. set_text_variables failing


## [1.6.3] - 2023-06-26
### Added
- General:
  - OS environment expansion in ${VAR}
  - Now outputs can request to be added to one or more groups (#435)
  - PCB text variables cached in the PCB are now reset when the config
    uses `set_text_variables`. This is a complex dilemma of KiCad 6/7
    policy implementation. See
    [KiCad issue 14360](https://gitlab.com/kicad/code/kicad/-/issues/14360).
    (#441)
  - Default values for @TAGS@
  - Parametrizable imports
- Command line:
  - `--list-variants` List all available variants (See #434)
  - `--only-names` to make `--list` list only output names
  - `--only-pre` to list only the preflights
  - `--only-groups` to list only the groups
  - `--output-name-first` to list outputs by name, no description (See #436)
- Global options:
  - `use_os_env_for_expand` to disable OS environment expansion
  - `environment`.`extra_os` to define environment variables
  - `field_voltage` Name/s of the field/s used for the voltage raiting
  - `field_package` Name/s of the field/s used for the package, not footprint
  - `field_temp_coef` Name/s of the field/s used for the temperature
     coefficient
  - `field_power` Name/s of the field/s used for the power raiting
  - `invalidate_pcb_text_cache` controls if we reset the text variables cached
    in the PCB file.
  - `git_diff_strategy` selects how we preserve the current repo state.
    (See #443)
- Filters:
  - New `value_split` to extract information from the Value field and put it in
    separated fields. I.e. tolerance, voltage, etc.
  - New `spec_to_field` to extract information from the distributors specs and
    put in fields. I.e. RoHS status.
  - New `generic` options `exclude_not_in_bom` and `exclude_not_on_board` to
    use KiCad 6+ flags. (See #429)
- Internal templates:
  - JLCPCB_with_THT and JLCPCB_stencil_with_THT: adding THT components.
- New internal filters:
  - `_value_split` splits the Value field but the field remains and the extra
    data is not visible
  - `_value_split_replace` splits the Value field and replaces it
- Internal templates:
  - CheckZoneFill: Used to check if a zone fill operation makes the PCB quite
    different (#431)
  - Versions with stencil for Elecrow, FusionPCB, P-Ban and PCBWay.
  - PanelDemo_4x4: Demo for a 4x4 panel.
- Render_3D:
  - `realistic`: can be used to disable the realistic colors and get the GUI ones
  - `show_board_body`: can be used to make the PCB core transparent (see inner)
  - `show_comments`: to see the content of the User.Comments layer.
  - `show_eco`: to see the content of the Eco1.User/Eco2.User layers.
  - `show_adhesive`: to see the content of the *.Adhesive layers.
- Navigate_Results:
  - `skip_not_run`: used to skip outputs not generated in default runs.
- Compress:
  - `skip_not_run`: used to skip outputs not generated in default runs.
- Position:
  - `quote_all`: forces quotes to all values in the CSV output. (See #456)

### Changed
- Command line:
  - `--list` also lists groups
- KiCad v6/7 schematic:
  - When saving an schematic the hierarchy is expanded only if needed,
    i.e. value of an instance changed
- List actions:
  - Now you must explicitly ask to configure outputs. Otherwise isn't needed.
    As a result you no longer need to have an SCH/PCB. Use `--config-outs` to
    get the old behavior.
- Git diff link file name:
  - Now we default to using worktrees instead of stash push/pop. As a side
    effect the names of the git points are chnaged. This is because main/master
    only applies to the main worktree. So the names now refer to the closest
    tag.
- JLCPCB_stencil: Is now just like JLCPCB. The only difference is the added
  layers.

### Fixed
- KiCad v6/7 schematic:
  - Net Class Flags not saved in variants or annotated schematics
  - Repeated UUIDs saved in variants
  - Bitmap scale not saved in variants or annotated schematics
  - `lib_name` attribute not saved in variants or annotated schematics
- Position:
  - Components marked as "Exclude from position files" not excluded when only
    SMD components are selected. (See #429)
- Diff:
  - KIBOT_TAG with n > 0 skipped n commits, not n tags (#430)
  - Details related to the project not applied during a diff involving a
    variant (project not copied) (#438)
- Copy files:
  - PCB not loaded if the only action was to copy the 3D models
  - Problems for STEP models when copying models
- Gerber:
  - Problems trying to compress gerbers for a board with inner layers when
    using legacy file extensions (#446)
- Electro-grammar:
  - Problems with floating point tolerances (i.e. 0.1%) (#447)
- KiCad user template directory autodetection for KiCad 7+

## [1.6.2] - 2023-04-24
### Added
- General:
  - Support for time stamp in the date (i.e. 2023-04-02T09:22-03:00)
  - Support to pass variables to the 3D models download URL (#414)
  - Support for netclass flags (#418)
  - Export KICADn_* environment variables for the older versions
    So you can use KICAD6_* variables on KiCad 7.
- Expansion patterns:
  - **%M** directory where the pcb/sch resides. Only the last component
    i.e. /a/b/c/name.kicad_pcb -> c  (#421)
- Command line:
  - `--banner N` Option to display a banner
  - `--log FILE` Option to log to a file, in addition to the stderr
- Global options:
  - `colored_tht_resistors` to disable the 3D colored resistors.
  - `field_tolerance` field/s to look for resistor tolerance.
  - `default_resistor_tolerance` which tolerance to use when none found.
  - `cache_3d_resistors` to avoid generating them all the time.
  - `resources_dir` to specify fonts and colors to install (CI/CD)
- 3D: colored 3D models for THT resistors
- Blender export:
  - Better default light
  - More light options
- Datasheet download: now the warnings mention which reference failed.
- Plot related outputs and PCB_Print:
  - `individual_page_scaling`: to control if the center of the page is computed
    using all pages or individually.
- Plot related outputs:
  - All outputs now support scaling.
- BoM:
  - Support for extra information in the *Value* field.
    Currently just parsed, not rejected.
- PCB/SCH parity test:
  - Check for value and fields/properties.
- SCH print:
  - Support for title change
- VRML:
  - Option to use the auxiliary origin as reference. (#420)

### Fixed
- Makefile: don't skip all preflights on each run, just the ones we generate
  as targets. (#405)
- KiKit present: problems when no board was specified. (#402)
- Datasheet download:
  - Avoid interruptions when too many redirections is detected (#408)
- PcbDraw:
  - KiCad 7.0.1 polygons used as board edge. (yaqwsx/PcbDraw#142)
- PCB Print:
  - Interference between the visible layers in the PRL file and the results
    when scaling. (#407)
  - Problems with images in the WKS (KiCad 5/6)
- Diff:
  - Problems when using an output and no variant specified.
- PCB/SCH parity test:
  - Workaround for bogus net codes generated by KiCad (#410)
- 3D Models:
  - Problems to download KiCad 7 models (#417)
  - Added workaround for KiCad 7 failing to export VRMLs for PCBs using paths
    relative to the footprint. (See #417)
- VRML:
  - ref_y coordinate not used. (#419)

### Changed:
- Some R, L and C values that were rejected are accepted now. You just get a
  warning about what part of the value was discarded.


## [1.6.1] - 2023-03-16
### Added
- KiCad 7.0.1 support
- Global options:
  - `allow_blind_buried_vias` and `allow_microvias` for KiCad 7 (no longer in
     KiCad)
  - `erc_grid` to specify the grid size for KiCad 7 ERC tests
- Report:
  - Counters for total vias and by via type (`vias_count`, `thru_vias_count`,
    `blind_vias_count` and `micro_vias_count`)
  - Warnings when micro and/or blind vias aren't allowed, but we found them.
- KiCad 7 specific:
  - Avoid warnings about missing coutyard for footprints marked as excluded
    from courtyard tests.
  - `kicad_dnp_applied` global option to use the *Do Not Populate* schematic
    flag as *do not fit* for KiBot, enabled by default.
  - `kicad_dnp_applies_to_3D` global option to eliminate the 3D models of
    components marked as *Do Not Populate*. This option applies to the case
    where no filter or variants are in use. Enabled by default. The
    `kicad_dnp_applied` option also disables it.
  - `cross_using_kicad` global option to use KiCad to cross DNP components in
    the schematic. Enabled by default.

### Fixed
- Problems to detect the schematic name when the path to the config contained a
  dot that isn't used for an extension and some particular conditions were met.
- PCB Print: KiCad crashing on some complex filled zones (#396)

## [1.6.0] - 2023-02-06
### Added
- General:
  - Support for `groups` of `outputs`
  - Internal templates import
  - Better support for wrong pre-flight options (#360)
  - A mechanism to cache downloaded 3D models
  - Support to download 3D models from EasyEDA (using LCSC codes)
- Global options:
  - field_lcsc_part: to select the LCSC/JLCPCB part field
- New outputs:
  - `vrml` export the 3D model in Virtual Reality Modeling Language (#349)
  - `ps_sch_print`, `dxf_sch_print` and `hpgl_sch_print` variants of
    `pdf_sch_print`
  - `blender_export` exports the PCB to Blender and other 3D formats,
     renders the PCB with impressive quality (experimental)
- New internal filters:
  - `_only_smd` used to get only SMD parts
  - `_only_tht` used to get only THT parts
  - `_only_virtual` used to get only virtual parts
- Variants:
  - Support for multi-boards as defined by KiKit
- Internal templates:
  - FusionPCB: gerber, drill and compress
  - Elecrow: gerber, drill and compress
  - JLCPCB: gerber, drill, position, BoM and compress
  - MacroFab_XYRS: XYRS position file compatible with MacroFab
  - P-Ban: gerber, drill and compress
  - PCB2Blender_2_1: generates a pcb2blender 2.1 file to import on Blender
    (See #349)
  - PCB2Blender_2_1_haschtl: PCB2Blender_2_1 variant for @Haschtl fork.
  - PCBWay: gerber, drill and compress
- Compress:
  - Option to use the output's `dir` as reference (`from_output_dir`)
- iBoM:
  - `hide_excluded` to hide excluded *.Fab drawings.
- PCB_Print:
  - Added a mechanism to create a page for each copper layer. (#365)
- Plot related outputs and PCB_Print:
  - Added support for the KiCad 6 "sketch_pads_on_fab_layers" option. (#356)
- Report:
  - Expansion for KiCad text variables and environment variables (See #368)
- *SCH_Print:
  - Added options to select the color theme and enable background color. (#362)
- SVG:
  - Options to limit the view box to the used area.
### Fixed
- BoM:
  - pre_transform filers can't be logic filters
- Copy_Files:
  - Problems on KiCad 5 (no 3rd party dir) (#357)
  - Problems with compress output (also Makefile) (#372)
- DOCs
  - annotate_pcb pre-flight missing options (#360)
  - annotate_pcb pre-flight wrong example (#360)
- iBoM:
  - Variant changes to the *.Fab weren't exported.
    Now all 2D variant stuff is applied before calling iBoM (#350)
- PCB_Print:
  - Images not showing in custom frames. (#352)
  - Problems when trying to use groups of layers (i.e. copper)
- Report:
  - Computed size when using circles and some arcs in the PCB edge (#375)
### Changed
- Downloaded 3D models are no longer discarded.
  They are stored in ~/.cache/kibot/3d
  You can change the directory using KIBOT_3D_MODELS
- License is now AGPL v3, since we are incorporating AGPL code.

## [1.5.1] - 2022-12-16
### Fixed
- System level resources look-up

## [1.5.0] - 2022-12-16
### Added
- New output:
  - `populate` to create step-by-step assembly instructions
    With support for `pcbdraw` and `render_3d`.
  - `panelize` to create a PCB panel containing N copies of the PCB.
  - `stencil_3d` to create 3D self-registering printable stencils.
  - `stencil_for_jig` to create steel stencils and 3D register.
  - `kikit_present` to create a project presentation web page.
- generic filters: options to filter by PCB side
- BoM:
  - Option to link to Mouser site.
  - Human readable text output format.
- Diff:
  - Option to compare only the first schematic page. (See #319)
- iBoM:
  - Support for the `offset_back_rotation` option
- Navigate Results:
  - Support for compress
- PcbDraw:
  - BMP output format
  - Image margin
  - Outline width
  - Solder paste removal
  - V-CUTS layer
  - Resistor remap and flip
  - A `remap_components` option with better type checks
  - Better support for variants
  - Option to control the *SVG precision* (units scale)
  - Filter expansion in `show_components` and `highlight`
- PCB_Print:
  - Option to control the *SVG precision* (units scale)
  - Now the text in the PDF is searchable. (#331)
  - Margins for the autoscale mode. (#337)
- Render_3D:
  - Option to render only some components (like in PcbDraw)
  - Option to auto-crop the resulting PNG
  - Option to make transparent the background
  - Option to highlight components
- SVG:
  - Option to control the *SVG precision* (units scale)

### Changed
- Diff:
  - Now the default is to compare all the schematic pages. (#319)
- Report:
  - loss tangent decimals, added one more.

### Fixed
- QR lib update: Problems when moving the footprint to the bottom for
  KiCad 5.
- SVG, PCB_Print, PcbDraw: Problems to display the outputs using Chrome and
  Firefox.
- Diff: Problems when comparing to a repo point where the PCB/SCH didn't exist
  yet. (#323)
- Report: Problems when using NPTH holes with sizes that doesn't correspond to
  real drill tools. It generated bogus reports about wrong OARs. (#326)
- Problems when using more than one dielectric in the stack-up. (#328)
- Gerber: Extension used for JLCPCB inner layers. (#329)
- BoM:
  - The length of the CSV separator is now validated.
  - Using \t, \n, \r and \\ is now supported. (See #334)
  - Digi-key link in the HTML output.
- KiBoM: User defined fields wasn't available as column names. (#344)
- Imports:
  - Problems with recursive imports when the intermediate import didn't
    contain any of the requested elements (i.e. no outputs). (#335)
- Navigate results: fail when no output to generate. Now you get a warning.
- Makefile: outputs marked as not run by default were listed in the `all`
  target.

## [1.4.0] - 2022-10-12
### Added
- General things:
  - Some basic preprocessing, now you can parametrize the YAML config.
    (See #233 #243)
  - Support for 3D models aliases and also a global option to define
    them in the KiBot configuration (See #261)
  - Environment and text variables now can be used as 3D model aliases.
    (See #261)
  - Environment and text variables expansion is now recursive.
    So in `${VAR}` the *VAR* can contain `${OTHER_VAR}`
  - Command line option to specify warnings to be excluded. Useful for
    warnings issued before applying the global options (i.e during
    import). (#296)
  - `pre_transform` filter to outputs supporting variants.
- New outputs:
  - PCB_Variant: saves a PCB with filters and variants applied.
  - Copy_Files: used to copy files to the output directory. (#279)
                You can also copy the 3D models.
- Support for Eurocircuits drill adjust to fix small OARs.
  Option `eurocircuits_reduce_holes`. (#227)
- Global options:
  - Support for changing text variables with variants during outputs creation.
    Option `set_text_variables_before_output`. (See #233)
  - Options to control which stuff is changed on PCB variants: (See #270)
    - cross_footprints_for_dnp
    - remove_adhesive_for_dnp
    - remove_solder_paste_for_dnp
    - hide_excluded (default value)
  - Mechanism to give more priority to local globals. (See #291)
- Diff:
  - Mechanism to compare using a variant (See #278)
  - Mechanism to specify the current PCB/Schematic in memory (See #295)
  - Mechanism to compare with the last Nth tag (See #312)
  - Option to skip pages with no differences
- Sch Variant:
  - Option to copy the project. Needed for text variables.
  - Option to change the title (similar to PCB Variant)
- Render_3D: Options to disable some technical layers and control the
  silkscreen clipping. (#282)
- Internal BoM:
  - Now you can aggregate components using CSV files. (See #248)
  - Added some basic support for "Exclude from BoM" flag (See #316)
- Now you can check PCB and schematic parity using the `update_xml` preflight
  (See #297)
- New filters:
  - `urlify` to convert URLs in fields to HTML links (#311)
  - `field_modify` a more generic field transformer
- Position: option to set the resolution for floating values (#314)

### Fixed
- Problems to compress netlists. (#287)
- 2D PCB processing didn't show in 3D targets (i.e. solder paste not removed in
  the 3D render). (See #270)
- KiBot exited when downloading a datasheet and got a connection error
  (#289 #290)
- KiCad 5 "assert "lower <= upper" failed in Clamp()" (#304)
- Missing XYRS information for components with multiple units (#306)
- Schematic v6:
  - Problems when creating a variant of a sub-sheet that was edited as a
    standalone sheet (#307)
  - Autoplace fields could be lost in variants.
- iBoM: Name displayed in the HTML when using filters and/or variants.
- Position: Components wrongly separated by side when the side column wasn't
  the last column (#313)

### Changed
- Diff:
  - When comparing a file now the links says Current/FILE instead of None
  - The default was to compare the current file on storage, now is the current
    file on memory. It includes the zone refill indicated in the preflights.
    (See #295)
  - Now the error about differences bigger than the threshold is more clear.
    KiBot also returns a distinct error level.
- Now the global `dir` option also applies to the preflights, can be disabled
  using `use_dir_for_preflights`. (#292)
- When importing globals now options that are lists or dicts are merged, not
  just replaced. (#291)


## [1.3.0] - 2022-09-08
### Added
- New outputs:
  - Diff: to compute differences between PCBs and SCHs. (INTI-CMNB/KiAuto#14)
  - Info: collects info about the environment. (See #209)
- Try to download missing tools and Python modules.
  The user also gets more information when something is missing.
  It can be disabled from the command line.
- Global options:
  - Cross components without a body (#219)
  - Restore the project at exit (#250)
- Imports:
  - Now you can nest imports (import from an imported file) (#218)
  - Preflights can be imported (#181)
- `--dont-stop` command line option, to try to continue even on errors (#209)
- PDF/SVG PCB Print: option to print all pages/single page (#236)
- iBoM: Support for variants that change component fields (#242)
- Workaround for problems with DRC exclusions (See INTI-CMNB/KiAuto#26, #250)
  Global option: `drc_exclusions_workaround`
  KiCad bug [11562](https://gitlab.com/kicad/code/kicad/-/issues/11562)
- Internal BoM: KiCad 6 text variables expansion in the fields (#247)
- Compress: Option to store symlinks. (See #265)
- PCB Print:
  - Option to configure the forced edge color. (#281)
  - Option to control the resolution (DPI). (See #259)
  - Option to move the page number to the extension (page_number_as_extension)
    (See #283)
  - Option to customize the page numbers (See #283)
- Installation checker: option to show the tool paths.

### Fixed
- OAR computation (Report) (#225)
- Position: Problems when doing manual panelization (repeated references) (#224)
- PCB_Print:
  - Problems with filtered/modified PCBs
  - Problems with zones on multiple layers (#226)
  - Problems with `hide_excluded: true` and components not in the SCH (#258)
  - Text vars generated in the same run didn't show up (#280)
  - Low resolution for the solder mask. (See #259)
- SCH Variants on KiCad 6: Problems with missing values in the title block.
- Report: Converted file wasn't stored at `dir` (#238)
- Datasheet download: Time-outs on some servers expecting modern browsers (#240)
- SCH Print and Netlist: name collisions. When the default name used by KiCad
  belongs to an already existing file. (#244)
- Install checker: fixed problems to detect iBoM installed as plugin. (#209)
- Internal Netlist generation (i.e. iBoM with variants): problems withg
  components that doesn't specify a library. (See #242)
- Problems when setting a text variable to an empty string. (#268)
- QR lib update: Problems when moving the footprint to the bottom. (#271)
- Misleading messages for missing 3D models that starts with ${VAR} when VAR
  isn't defined. The old code tried to make it an absolute path.

### Changed
- The order in which main sections are parsed is now fixed.
  The declared order is ignored. The order is:
  kiplot/kibot, import, global, filters, variants, preflight, outputs
- Datasheet download:
  - Continue downloading if an SSL certificate error found (#239)
- PCB_Print: PNGs no longer has transparent background. This is because now we
  use a PDF as intermediate step.
- Fails to expand KiCad vars are reported once (not every time)
- No more warnings about missing 3D models when we can download them


## [1.2.0] - 2022-06-15
### Added
- The outputs help now display the more relevant options first and highlighted.
  Which ones are more relevant is somehow arbitrary, comments are welcome.
- General stuff:
  - Outputs now can have priorities, by default is applied.
    Use `-n` to disable it.
- New outputs:
  - `navigate_results` creates web pages to browse the generated outputs.
     [Example](https://inti-cmnb.github.io/kibot_variants_arduprog_site/Browse/t1-navigate.html)
- New globals:
  - `environment` section allows defining KiCad environment variables.
    (See INTI-CMNB/KiAuto#21)
- GitHub discussions are now enabled. Comment about your KiBot experience
  [here](https://github.com/INTI-CMNB/KiBot/discussions)

### Fixed
- Components with mounting hole where excluded (#201)
- GenCAD output targets.
- Problems expanding multiple KiCad variables in the same value.
- XML BoM: Fixed problems with fields containing / (#206)
- pcb_print: vias processing was disabled.
- pcb_print: problems with frame in GUI mode and portrait page orientation.
- svg_pcb_print: page orientation for portrait.

### Changed
- KiCad environment variables: more variables detected, native KiCad 6 names,
  all exported to the environment (#205)
- Consequences of the priorities implementation:
  - `qr_lib` outputs are created before others
  - `navigate_results` and `compress` outputs are created after others

## [1.1.0] - 2022-05-24
### Added
- `kibot-check` tool to check the installation
- New outputs:
  - KiCad netlist generation
  - IPC-D-356 netlist generation (#197)
- Internal BoM:
  - Pattern and text variables expansion in the title (#198)
  - Customizable extra info after the title (#199)

### Fixed
- Already configured outputs not created (i.e. when creating reports)
- KiCost+Internal variants: UTF-8 problems
- KiCost+Internal variants: problem with `variant` field capitalization

## [1.0.0] - 2022-05-10
### Added
- General stuff:
  - KiCad 6 support
  - Import mechanism for filters, variants and globals (#88)
  - Outputs can use the options of other outputs as base (extend them). (#112)
  - A mechanism to avoid running some outputs by default. (#112)
  - `--cli-order` option to generate outputs in arbitrary order. (#106)
  - `--quick-start` option to create usable configs and outputs.
- Filters and variants:
  - Options to better control the rotation filter (#60 and #67):
    - invert_bottom: bottom angles are inverted.
    - skip_top: top components aren't rotated.
    - skip_bottom: bottom components aren't rotated.
  - Generic filter: options to match if a field is/isn't defined.
  - Another experimental mechanism to change 3D models according to the variant.
    (#103)
  - Support for variants on KiCost output. (#106)
- Expansion patterns:
  - **%g** the `file_id` of the global variant.
  - **%G** the `name` of the global variant.
  - **%C1**, **%C2**, **%C3** and **%C4** the comments in the sch/pcb title
    block.
  - **%bc**, **%bC1**, **%bC2**, **%bC3**, **%bC4**, **%bd**, **%bf**,
    **%bF**, **%bp** and **%br** board data
  - **%sc**, **%sC1**, **%sC2**, **%sC3**, **%sC4**, **%sd**, **%sf**,
    **%sF**, **%sp** and **%sr** schematic data
  - **%V** the variant name
  - **%I** user defined ID for this output
  - Now patterns are also expanded in the out_dir name.
- Global options:
  - Default global `dir` option.
  - Default global `units` option.
  - Global option to specify `out_dir` (like -d command line option)
  - Global options to control the date format.
  - Added global options to define the PCB details (`pcb_material`,
    `solder_mask_color`, `silk_screen_color` and `pcb_finish`)
- New preflights:
  - Commands to replace tags in the schematic and PCB (KiCad 5). (#93)
    Also a mechanism to define variables in KiCad 6. (#161)
  - Annotate power components. (#76)
  - Annotate according to PCB coordinates (#93)
- New outputs:
  - 3D view render
  - Report generation (for design house) (#93)
  - QR codes generation and update: symbols and footprints. (#93)
  - Print PCB layers in SVG/PDF/PS/EPS/PNG format.
  - Join PDFs. (#156)
  - Export PCB in GENCAD format. (#159)
  - Datasheet downloader. (#119)
- XLSX BoM: option to control the logo scale (#84)
- PDF/SVG PCB Print:
  - option `hide_excluded` to hide components marked by the `exclude_filter`.
    https://forum.kicad.info/t/fab-drawing-for-only-through-hole-parts/
  - mechanism to change the block title. (#102)
  - KiCad 6 color theme selection.
  - New `pcb_print` output with more flexibility and faster.
- Internal BoM:
  - option to avoid merging components with empty fields.
    Is named `merge_both_blank` and defaults to true.
  - when a `Value` field can't be interpreted as a `number+unit`,
    and it contain at least one space, now we try to use the text before the
    space. This helps for cases like "10K 1%".
  - `count_smd_tht` option to compute SMD/THT stats. (#113)
  - option to add text to the `join` list. (#108)
  - two other options for the sorting criteria.
  - XYRS support (you can generate position files using it)
  - CSV `hide_header` option
- Drill:
  - Excellon: added `route_mode_for_oval_holes` option.
  - Support for blind/buried vias. (#166)
- SCH PDF Print: monochrome and no frame options.
- Compress:
  - Now you can compress files relative to the current working directory.
    So you can create a compressed file containing the source schematic and
    PCB files. (#93)
  - Added an option to remove the files we compressed. (#192)
- Support for new KiCost options `split_extra_fields` and `board_qty`. (#120)
- Position files now can include virtual components. (#106)
- Support for `--subst-models` option for KiCad 6's kicad2step. (#137)

### Changed
- Internal BoM: now components with different Tolerance, Voltage, Current
  and/or Power fields aren't grouped together.
  These fields are now part of the default `group_fields`. (#79)
- JLCPCB example, to match current recommendations
  (g200kg/kicad-gerberzipper#11)
- Internal BoM: the field used for variants doesn't produce conflicts. (#100)
- The `%v/%V` expansion patterns now expand to the global variant when used in
  a context not related to variants. I.e. when a `compress` target expands
  `%v`.
- Now you get an error when defining two outputs with the same name.
- The `%d/%sd/%bd` expansion patterns are now affected by the global `date_format`.
  Can be disabled using `date_reformat: false`. (#121)
- The default output pattern now includes the `output_id` (%I)
- The `source` path for `compress` now has pattern expansion (#152)

### Fixed
- Position files now defaults to use the auxiliary origin as KiCad.
  Can be disabled to use absolute coordinates. (#87)
- Board View:
  - flipped output. (#89)
  - problems with netnames using spaces. (#90)
  - get_targets not implemented. (#167)
- Schematic
  - load: problems with fields containing double quotes. (#98)
  - Paper orientation was discarded on v5 files. (#150)
- `--list`: problems with layers and fields specific for the project.
  (INTI-CMNB/kibot_variants_arduprog#4)
- Makefile: %VALUE not expanded in the directory targets.
- KiCost variants:
  - empty DNF fields shouldn't be excluded. (#101)
  - problems when setting a field in a variant that doesn't
    exist when no variant is selected. (#105)
- KiCost: list arguments wrongly passed. (#120)
- PCB Print: to show the real name of the PCB file. (#102)
- Compress: not expanding %VALUES in target dirs. (#111)
- Gerber: job file didn't use the global output pattern. (#116)
- Warnings count
- Update XML: Removed the side effect Bom. (#106)
- Problems when using a hidden config file, using an output that needs the SCH,
  not specifying the SCH and more than one SCH was found. (#138)
- 3D: problems to download 3D models for native KiCad 6 files. (#171)
      (not imported from KiCad 5)
- Problems when using page layout files with relative paths. (#174)


## [0.11.0] - 2021-04-25
### Added
- `erc_warnings` preflight option to consider ERC warnings as errors.
- Pattern expansion in the `dir` option for outputs (#58)
- New filter types:
  - `suparts`: Adds support for KiCost's subparts feature.
  - `field_rename`: Used to rename schematic fields.
  - `var_rename_kicost`: Like `var_rename` but using KiCost mechanism.
- New KiCost variant style.
- `skip_if_no_field` and `invert` options to the regex used in the generic
  filter.
- Board view file format export (#69)
- Experimental mechanism to change 3D models according to the variant.
- Support for width, style and color in "wire notes" (#70)
- Level and comment to columns in the XLSX BoM output.
- Basic KiCost support (**experimental**).
- Basic internal BoM and KiCost integration (**experimental**).

### Changed
- Errors and warnings from KiAuto now are printed as errors and warnings.
- Schematic dependencies are sorted in the generated Makefiles.
- Makefile variables KIBOT, DEBUG and LOGFILE can be defined from outside.
- Reference ranges of two elements no longer represented as ranges.
  Examples: "R1-R2" is now "R1 R2", "R1-R3" remains unchanged.

### Fixed
- Problem when using E/DRC filters and the output dir didn't exist.
- Not all errors during makefile generation were caught (got a stack trace).
- Output dirs created when generating a makefile for a compress target.
- Problems with some SnapEDA libs (extra space in lib termination tag #57)
- The "References" (plural) column is now coloured as "Reference" (singular)

## [0.10.1] - 2021-02-22
### Added
- GitLab CI workaround
- Verbosity level is now passed to KiAuto

## [0.10.0-4] - 2021-02-16
### Fixed
- Problem using Python 3.6 (ZipFile's compresslevel arg needs 3.7)

## [0.10.0-3] - 2021-02-16
### Fixed
- Problem using Python 3.6 (StreamHandler.setStream introduced in 3.7)

## [0.10.0-2] - 2021-02-12
### Fixed
- Missing python3-distutils dependency on Debian package.

## [0.10.0] - 2021-02-12
### Added
- The multipart id to references of multipart components others than part 1.
- Internal BoM:
  - `no_conflict` option to exclude fields from conflict detection.
  - HTML tables can be sorted selecting a column (Java Script).
  - You can consolidate more than one project in one BoM.
- Support for KICAD_CONFIG_HOME defined from inside KiCad.
- Now layers can be selected using the default KiCad names.
- More control over the name of the drill and gerber files.
- More options to customize the excellon output.
- Custom reports for plot outputs (i.e. custom gerber job generation)
- Example configurations for gerber and drill files for:
  - [Elecrow](https://www.elecrow.com/)
  - [FusionPCB](https://www.seeedstudio.io/fusion.html)
  - [JLCPCB](https://jlcpcb.com/)
  - [P-Ban](https://www.p-ban.com/)
  - [PCBWay](https://www.pcbway.com)
- Support for ZIP/TAR/RAR generation.
- Makefile generation.
- KiAuto time-out control.
- Now you can import outputs from another config file.

### Changed
- Now the default output name applies to the DRC and ERC report names.
  This provides more coherent file names.
- Internal BoM: The "Quantity" column no longer includes the DNF/C status.
  This status was moved to a separated column named `Status`.
  You can join both columns if you want.
- Internal BoM: HTML rows are highlighted on hover (not just the cell).
- Now information messages go to stdout (not stderr).
  Debug, warning and error messages still use stderr.
- Now InteractiveHtmlBom can be installed just as a plugin.

### Fixed
- Extra data about drill marks in gerber files.
- Problems using internal names for drill maps in gerb_drill output (#47).
- Problems using layer suffixes containing non-ASCII chars (i.e. UTF-8).
- Problems when using components with more than 10 subparts.


## [0.9.0] - 2021-01-04
### Added
- iBoM output: file name patterns are allowed for the `netlist_file` option.
- File name patterns: %F is the name of the source file without extension, but
  with the path.
- A hint for pip installations without using `--no-compile`.
- Support to field overwrite according to variant.
- Support to generate negative X positions for the bottom layer.
- A filter to rotate footprints in the position file (#28).
- The step output now can download missing 3D models.

### Changed
- Now position files are naturally sorted (R10 after R9, not after R1)
- Position files in CSV format quotes only the columns that could contain an
  space. Just like KiCad does.

### Fixed
- Now we support missing field names in schematic library entries.
- Generic filter `include_only` option worked only when debug enabled.

## [0.8.1] - 2020-12-09
### Added
- Internal BoM HTML: highlight cell when hover.
- Internal BoM HTML: allow to jump to REF of row number using anchors.

### Fixed
- Internal BoM separator wasn't applied when using `use_alt`
- Problems loading plug-ins when using `pip`.

## [0.8.0] - 2020-11-06
### Added
- The KiBoM and internal BoM generators now support configuring the
  separator used for the list of references.
- Help for filters and variants.
- Support for new `pcbnew_do export` options.
- Filters for KiBot warnings.
- Columns in position files can be selected, renamed and sorted as you
  like.

### Fixed
- KiBom variants when using multiple variants and a component uses more
  than one, specifying opposite rules.
- Problems when using the `pdf_pcb_print` output and variants to remove
  a component with ridiculous pads that only has solder paste (no
  copper, nor even solder mask aperture).
- Excellon drill output when using unified output and not using default
  KiCad names.


## [0.7.0] - 2020-09-11
### Added
- Now variants are separated entities. Two flavors implemented: KiBoM
  and IBoM.
- New filters entities. They work in complement with variants.
  All the filtering functionality found in KiBoM and IBoM is supported.
- Most outputs now supports variants. You can:
  - Mark not fitted components with a cross in the schematic
  - Mark not fitted components with a cross in the *.Fab layers of the
    PCB
  - Remove solder paste from not fitted components
  - Remove adhesive glue from not fitted components
  - Exclude components from the BoM (also mark them as DNF and/or DNC
    (Do Not Change))
  - Exclude components from the interactive BoM
  - Remove not fitted components from the STEP file
  - Exclude components from the position (pick & place) file
- Default output file name format and default variant can be specified
  from the command line.

### Fixed
- Virtual components are always excluded from position files.
  Note you can change it using the variants mechanism.

## [0.6.2] - 2020-08-25
### Changed
- Discarded spaces at the beginning and end of user fields when creating the
  internal BoM. They are usually mistakes that prevents grouping components.

### Fixed
- The variants logic for BoMs when a component resquested to be only added to
  more than one variant.
- Removed warnings about malformed values for DNF components indicating it in
  its value.
- Problems with PcbDraw when generating PNG and JPG outputs. Now we use a more
  reliable conversion method when available.

## [0.6.1] - 2020-08-20
### Added
- More robust behavior on GUI dependent commands.

### Changed
- Incorporated mcpy, no longer a dependency.

### Fixed
- Problems when using `pip install` without --no-compile.
  At least for user level install.

## [0.6.0] - 2020-08-18
### Added
- Internal BoM generator, based on KiBoM code.
  This generator doesn't need the netlist, works directly from the SCH.
  It features enhanced HTML and XLSX outputs, in addition to the CSV, TSV, TXT
  and XML traditional outputs.
- Support for full KiBoM configuration from the YAML
- Added output to print to an SVG file.
- Added default output file name pattern. Can be applied to all outputs.
- Unified output name:
  - `pdf_pcb_print.output` can be used instead of `pdf_pcb_print.output_name`
  - `gerber.gerber_job_file` option to control the gerber job file name.
  - `output` option to control the file name to all plot output formats.
  - `drill`, `drill.map` and `position` file names can be configured.
  - Output file names supports expansion of various interesting values (base
    name, sheet title, revision, etc.).
- The filters now accept the following aliases (suggested by @leoheck):
  - `filter_msg` -> `filter`
  - `error_number` -> `number`
  - `regexp` -> `regex`

### Changed
- Default file names for:
  - pdf_pcb_print: includes the used layers
  - drill maps: uses drill instead of drl
  - drill: uses drill instead of drl, used in gbr and drl.
  - position: no -pos in CSVs
  - step: adds -3D
  - pdf_sch_print: adds -schematic
  - IBoM: contains the project name.

## [0.5.0] - 2020-07-11
### Changed
- Removed the "plot" option "check_zone_fills". Use the preflight option.
- Drill outputs: map.type and report.filename now should be map and report.
  The old mechanism is currently supported, but deprecated.
- Now the command line usage is more clearly documented, but also more strict.
- The --list option doesn't need a PCB file anymore.
  Note that passing it is now considered an error.
- Now we test the PCB and/or SCH only when we are doing something that needs
  them.

### Added
- The layers entry is much more flexible now.
  Many changes, read the README.md
- PcbDraw output.
- -e/--schematic option to specify any schematic (not just derived from the PCB
  name.
- -x/--example option to generate a complete configuration example.
- --example supports --copy-options to copy the plot options from the PCB file.
- Help for the supported outputs (--help-list-outputs, --help-outputs and
  --help-output)
- Help for the supported preflights (--help-preflights)
- Better YAML validation.
- Added HPGL options:
  - pen_number
  - pen_speed
- Added metric_units to DXF options
- Added KiBoM options
  - number
  - variant
  - conf
  - separator
- Added the following InteractiveHtmlBom options:
  - dark_mode
  - hide_pads
  - show_fabrication
  - hide_silkscreen
  - highlight_pin1
  - no_redraw_on_drag
  - board_rotation
  - checkboxes
  - bom_view
  - layer_view
  - include_tracks
  - include_nets
  - sort_order
  - no_blacklist_virtual
  - blacklist_empty_val
  - netlist_file
  - extra_fields
  - normalize_field_case
  - variant_field
  - variants_whitelist
  - variants_blacklist
  - dnp_field

### Fixed
- The `sketch_plot` option is now implemented.
- 'ignore_unconnected' preflight wasn't working.
- The report of hwo many ERC/DRC errors we found.

## [0.4.0] - 2020-06-17
### Added
- STEP 3D model generation
- Support for unpatched InteractiveHtmlBom

## [0.3.0] - 2020-06-14
### Added
- Better debug information when a BoM fails to be generated.
- Support for compressed YAML files.

### Changed
- Allow operations that doesn't involve a PCB to run if the PCB file is
  missing or corrupted.
- The 'check_zone_fills' option is now independent of 'run_drc'

### Fixed
- Error codes that overlapped.

## [0.2.5] - 2020-06-11
### Added
- Tolerate config files without outputs
- Mechanism to filter ERC/DRC errors

### Fixed
- All pcbnew plot formats generated gerber job files
- Most formats that needed layers didn't complain when omitted

## [0.2.4] - 2020-05-19
### Changed
- Now kicad-automation-scripts 1.3.1 or newer is needed.

### Fixed
- Problems for kibom and print_sch outputs when the PCB name included a path.

## [0.2.3] - 2020-04-23
### Added
- List available targets

## [0.2.2] - 2020-04-20
### Fixed
- KiBoM temporal files, now removed
- preflight tasks that didn't honor --out-dir

## [0.2.1] - 2020-04-18
### Fixed
- Problem when the excellon drill target directory didn't exist (now created)

## [0.2.0] - 2020-03-28
### Added
- Documentation for current functionality
- Now the -b and -c options are optional, we guess the values
- Inner layers sanitation, support for the names used in the PCB file
- Better error report
- Print the PCB and SCH in PDF format (we had plot)
- KiBoM and InteractiveHtmlBoM support
- Pre-flight: generation of the BoM in XML format
- Pre-flight: DRC and ERC
- Option to skip preflight actions
- Option to select which outputs will be generated
- Progress information
- --version option

### Fixed
- Debian dependencies

## [0.1.1] - 2020-03-13
### Added
- Pick & place position
- Debian package
- Gerber job generation
