.. index::
   pair: notes; gerber format

Notes about Gerber format
-------------------------

I found this topic poorly documented and quite complex. So here is what
I know, feel free to send me any corrections. Note that this is a very
dynamic topic and this text was written in november 2020.

The gerber format is controlled by
`Ucamco <https://www.ucamco.com/en/>`__, a leading manufacturer of
equipment and software for PCB fabrication. Even when this isn’t an open
standard they release the spec for free and interact with Jean-Pierre
Charras (father of KiCad). So KiCad support for gerber format is really
updated.

The gerber format evolved with time, here are the versions I know:

-  **RS-274D** obsolete version of the format.
-  **RS-274X** (aka **X1**) this is the *extended* version of the
   format. Is the most widely supported, but has some limitations.
-  **X2** this is the format currently recommended by Ucamco and the
   default for modern KiCad versions. This extension adds important
   meta-data to the files. It helps CAM operators to know what’s every
   drawing in the image. So you know which are pads, tracks, etc. And
   also more interesting information: impedance controlled tracks, the
   role of each file, etc. Using X2 you can know what is each file
   without the need of special names or file extensions. KiCad can
   generate drill files using X2.
-  **X3** this is the current draft. One interesting addition is the
   *Components* role. These files replaces the position files, adding
   important information about the footprint.

In addition to them is the spec for the **Gerber Job** file. This file
was introduced between X2 and X3, and is used to group all the gerber
files. The *gbrjob* file contains all the missing stack-up information.

KiCad 5 can generate X1, X2 and gerber job files, including drill
information in gerber format. KiCad 5.99 (6.0 pre-release) can also
generate X3 files (position files in gerber format).

As you can see the idea of Ucamco is to unify all fabrication
information in one format.

The **X2** format was designed in a way that software that fully
implement **X1** can just ignore the added meta-data. In an ideal world
you shouldn’t bother about it and generate **X2** files. Just use the
**gbr** file extension and a *gbrjob* file. The problem is with poorly
implemented CAM tools. In particular **CAM350**, used by various
important cheap China manufacturers. This software has known issues
interpretating aperture macros and some X2 data. If your manufacturer
has problems with your files check the following:

-  Put gerber, drill and position files in the same directory.
-  Disable **X2** extensions (``use_gerber_x2_attributes`` set to
   ``false``)
-  Use arcaic role mechanism (``use_protel_extensions`` set to ``true``)
-  Disable **aperture macros** (KiCad 6 only:
   ``disable_aperture_macros`` set to ``true``)

The
`kicad-gerberzipper <https://github.com/g200kg/kicad-gerberzipper>`__ is
an action plugin for KiCad oriented to help to generate gerber and drill
files for some manufacturers. I adapted the configurations from
kicad-gerberzipper to KiBot configurations, they are available as
:ref:`internal templates <import-templates>`
