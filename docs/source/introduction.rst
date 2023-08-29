.. index::
   single: introduction

Introduction
------------

KiBot is a program which helps you to generate the fabrication and
documentation files for your KiCad projects easily, repeatable, and most
of all, scriptably. This means you can use a Makefile to export your
KiCad PCBs just as needed, or do it in a CI/CD environment.

For example, it’s common that you might want for each board rev:

-  Check ERC/DRC one last time (using `KiCad Automation
   Scripts <https://github.com/INTI-CMNB/kicad-automation-scripts/>`__)
-  Gerbers, drills and drill maps for a fab in their favourite format
-  Fab docs for the assembler, including the BoM (Bill of Materials),
   costs spreadsheet and board view
-  Pick and place files
-  PCB 3D model in STEP, VRML and PCB3D formats
-  PCB 3D render in PNG format
-  Compare PCB/SCHs
-  Panelization
-  Stencil creation

You want to do this in a one-touch way, and make sure everything you
need to do so is securely saved in version control, not on the back of
an old datasheet.

KiBot lets you do this. The following picture depicts the data flow:

.. figure:: https://raw.githubusercontent.com/INTI-CMNB/KiBot/master/docs/images/Esquema.png
   :alt: KiBot workflow

   KiBot Logo

If you want to see this concept applied to a real world project visit
the `Spora CI/CD <https://github.com/INTI-CMNB/kicad-ci-test-spora>`__
example.

