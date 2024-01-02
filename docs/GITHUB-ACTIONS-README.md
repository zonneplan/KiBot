# Guide for using KiBot with GitHub Actions.
Author: @sethkaz

This is a guide for getting started using KiBot with GitHub Actions.

## Basics

[GitHub Actions](https://github.com/actions) is a CI system that runs on GitHub. It uses [YAML files](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html) to define what actions it will take. Unfortunately, some of the links between YAML lines and their associated actions are a bit cryptic.  This guide will try to shed light on those cryptic portions.

### Basic GitHub file

Must be located at `{repo root}/.github/workflows/{meaningful_name}.yml`

```yaml
name: KiBot_GitHub_Actions  # This is a name. It can be anything you want.
on: [push, pull_request]    # GitHub triggers for running this.  In this example it will run when anything is pushed to GitHub or a pull request is created.
jobs:   # List of jobs to be run.  Can be used to better organize steps.
  KiBot-Generation:  # This is a name. It can be anything you want.
    runs-on: ubuntu-latest  # Don't change
    container: ghcr.io/inti-cmnb/kicad7_auto_full:latest  # Don't Change, except if needing older version of KiCad.

    steps:
    - name: Checkout repo
      uses: actions/checkout@v3  # GitHub built-in repo checkout step.

    # Start of the KiBot steps
    - name: Run KiBot
      run: |
        kibot -e "project_name.kicad_sch"

    # Post KiBot steps (Optional).
    - name: Optionally do other things
      run: |
        echo "Run bash commands to do things like committing the files or adding them as artifacts"
```


### Basic KiBot file

This file will match the syntax and keywords described in the [readme](https://kibot.readthedocs.io/en/latest/).

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

## GitHub-specific details

The `uses: actions/checkout` refers to a specific repo, [GitHub Actions](https://github.com/actions).

## KiBot Specific details



## Caveats, Gotchyas, and Pitfalls

1. KiBot requires a `{meaningful_name}.kibot.yaml` file name scheme. You can also use `{meaningful_name}.kibot.yml`.

## Different ways of doing things

This section will try to describe some different options for doing things within KiBot and GitHub, and hope to explain pros and cons.

- TODO: Fill this out.
- TODO: (Topic) GitHub artifacts vs exports committed.
- TODO: (Topic) When to run KiBot??  ERC/DRC only vs full outputs.
