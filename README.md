# KiPlot

KiPlot is a program which helps you to plot your KiCad PCBs to output
formats easily, repeatable, and most of all, scriptably. This means you
can use a Makefile to export your KiCad PCBs just as needed.

For example, it's common that you might want for each board rev:

* Check DRC one last time (use [KiCad Automation Scripts](https://github.com/INTI-CMNB/kicad-automation-scripts/))
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

## Using KiPlot

You can call `kiplot` directly, passing a PCB file and a config file:

```
kiplot -b $(PCB) -c $(KIPLOT_CFG) -v
```

A simple target can be added to your `makefile`, so you can just run
`make pcb_files` or integrate into your current build process.

```
pcb_files:
    kiplot -b $(PCB) -c $(KIPLOT_CFG) -v
```

## Installing

### Installation on Ubuntu/Debian:

Get the Debian package from the [releases section](https://github.com/INTI-CMNB/kiplot/releases) and run:
```
sudo apt install ./kiplot.inti-cmnb_*_all.deb
```


