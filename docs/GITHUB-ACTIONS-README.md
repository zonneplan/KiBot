# Guide for using KiBot with Github Actions.

This is a guide for getting started using KiBOT with Github Actions.

## Basics

[Github Actions](https://github.com/actions) is a CI system that runs on Github. It uses [YAML files](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html) to define what actions it will take. Unfortunately, some of the links between YAML lines and their associated actions are a bit cryptic.  This guide will try to shed light on those cyptic portions.

### Basic github file

Must be located at `{repo root}/.github/workflows/{meaningful_name}.yml
```yaml
name: KiBot_GitHub_Actions  # This is a name. It can be anything you want.
on: [push, pull_request]    # github triggers for running this.  In this example it will run when anything is pushed to github or a pull request is created.
jobs:   # List of jobs to be run.  Can be used to better organize steps.
  KiBot-Generation:  # This is a name. It can be anything you want.
    runs-on: ubuntu-latest  # Don't change
    container: ghcr.io/inti-cmnb/kicad7_auto:latest  # Don't Change, except if needing older version of KiCAD.

    steps:  
    - name: Checkout repo
      uses: actions/checkout@v3  # Github built-in repo checkout step.

    # Start of the KiBot steps
    - name: Run KiBot
      run: |
        kibot -e "project_name.kicad_sch"

    # Post KiBot steps (Optional).  
    - name: Optionally do other things
      run: |
        ECHO Run bash commands to do things like commiting the files or adding them as artifacts
```


### Basic KiBot file
This file will match the syntax and keywords described in the [readme](../README.md). 
```yaml
kibot:
  version: 1

preflight:
  run_erc: true
  run_drc: true
  check_zone_fills: true

outputs:
  - name: 'Print Schema as PDF'
    comment: "Print schematic (PDF)"
    type: pdf_sch_print
    dir: schematics
    options:
      output: '%p-Schematic.%x'
```

## Github-specific details

The `uses: actions/checkout` refers to a specific repo, [Github Actions](https://github.com/actions). 

## KiBot Specific details



## Caveats, Gotchyas, and Pitfalls

1. KiBot requires a `{meaningful_name}.kibot.yaml` file name scheme.  While most places use `*.yml` and `*.yaml` interchangeably, it is specific here that `*.kibot.yml` won't work. This is especially odd since github uses `*.yml` and kibot uses `*.yaml`. 

## Different ways of doing things

This section will try to describe some different options for doing things within KiBot and Github, and hope to explain pros and cons.

TODO: Fill this out.
TODO: (Topic) github artifacts vs exports commited.
TODO: (Topic) When to run KiBOT??  ERC/DRC only vs full outputs.
