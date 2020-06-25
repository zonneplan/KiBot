# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]
### Changed
- Removed the "plot" option "check_zone_fills". Use the preflight option.
- Drill outputs: map.type and report.filename now should be map and report.
  The old mechanism is currently supported, but deprecated.

### Added
- Help for the supported outputs (--help-list-outputs, --help-outputs and
  --help-output)
- Help for the supported preflights (--help-preflights)
- Better YAML validation.

### Fixed
- The `sketch_plot` option is now implemented.

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
- Most formats that needed layers didn't complain when ommited

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
- pre-flight tasks that didn't honor --out-dir

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
- Option to skip pre-flight actions
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

