# PcbDraw code

## Why?

- Important dependency: PcbDraw is currently a core functionality of KiBot because its used for the `pcb_print` output
- Increased number of dependencies: The upstream code pulls too much dependencies, some of them optional, others that we don't need.
  This is a constant problem.
- Incompatible interface and behavior: This should be fixed now that 1.0.0 is out, but I don't agree with the idea of doing small
  changes just because they look more elegant.
- Now integrable: This is one of the changes in 1.0.0, now the code is easier to call as module.
- Repeated functionality: The `render` stuff is already implemented by KiAuto.

## Details

Currently only the `plot` module is included.

### unit.py

- Replaced `unit` code.
  - So we have only one units conversion
  - I think the only difference is that KiBot code currently supports the locales decimal point

### plot.py

- Made the `pcbdraw` import relative
- Disabled `shrink_svg` by default
  - Pulls a problematic dependency: numpy
  - We keep the margin addition
  - The svgpathtool computation can be optionally enabled (plotter.compute_bbox)
- Changed calls to `ComputeBoundingBox()` to optionally use `aBoardEdgesOnly=True`
  - To get the same behavior as 0.9.0-5
  - This changes the size of the SVG to the size of the board
  - Controlled by plotter.kicad_bb_only_edge
  - We now also store the bbox in the plotter.boardsize member, avoiding repeated calls to KiCad API
- Added `no_warn_back` option to disable warnings on the opposite side

```diff
@@ -813,6 +813,7 @@
     highlight: Callable[[str], bool] = lambda x: False # References to highlight
     remapping: Callable[[str, str, str], Tuple[str, str]] = lambda ref, lib, name: (lib, name)
     resistor_values: Dict[str, ResistorValue] = field(default_factory=dict)
+    no_warn_back: bool = False

     def render(self, plotter: PcbPlotter) -> None:
         self._plotter = plotter
@@ -848,7 +849,8 @@
         else:
             ret = self._create_component(lib, name, ref, value)
             if ret is None:
-                self._plotter.yield_warning("component", f"Component {lib}:{name} has not footprint.")
+                if name[-5:] != '.back' or not self.no_warn_back:
+                    self._plotter.yield_warning("component", f"Component {lib}:{name} has not footprint.")
                 return
             component_element, component_info = ret
             self._used_components[unique_name] = component_info
```

- Added option to plot only the solder mask. The PCB_Print output uses it and plotting all the stuff looks stupid.
  The patch added too much nested conditionals so I moved the information to data structures.
  The patch looks big, but is just a mechanism to skip the unneeded layers.

```diff
diff --git a/kibot/PcbDraw/plot.py b/kibot/PcbDraw/plot.py
index af473cdb..f8990722 100644
--- a/kibot/PcbDraw/plot.py
+++ b/kibot/PcbDraw/plot.py
@@ -648,35 +648,44 @@ class PlotInterface:
         raise NotImplementedError("Plot interface wasn't implemented")
 
 
+SUBSTRATE_ELEMENTS = {
+    "board": (pcbnew.Edge_Cuts, pcbnew.Edge_Cuts),
+    "clad": (pcbnew.F_Mask, pcbnew.B_Mask),
+    "copper": (pcbnew.F_Cu, pcbnew.B_Cu),
+    "pads": (pcbnew.F_Cu, pcbnew.B_Cu),
+    "pads-mask": (pcbnew.F_Mask, pcbnew.B_Mask),
+    "silk": (pcbnew.F_SilkS, pcbnew.B_SilkS),
+    "outline": (pcbnew.Edge_Cuts, pcbnew.Edge_Cuts)
+}
+ELEMENTS_USED = (
+    # Normal plot, all the elements
+    ("board", "clad", "copper", "pads", "pads-mask", "silk", "outline"),
+    # Solder mask plot
+    ("board", "pads-mask")
+)
+
+
 @dataclass
 class PlotSubstrate(PlotInterface):
     drill_holes: bool = True
     outline_width: int = mm2ki(0.1)
+    only_mask: bool = False
 
     def render(self, plotter: PcbPlotter) -> None:
         self._plotter = plotter # ...so we don't have to pass it explicitly
+        SUBSTRATE_PROCESS = {
+            "board": self._process_baselayer,
+            "clad": self._process_layer,
+            "copper": self._process_layer,
+            "pads": self._process_layer,
+            "pads-mask": self._process_mask,
+            "silk": self._process_layer,
+            "outline": self._process_outline
+        }
 
         to_plot: List[PlotAction] = []
-        if plotter.render_back:
-            to_plot = [
-                PlotAction("board", [pcbnew.Edge_Cuts], self._process_baselayer),
-                PlotAction("clad", [pcbnew.B_Mask], self._process_layer),
-                PlotAction("copper", [pcbnew.B_Cu], self._process_layer),
-                PlotAction("pads", [pcbnew.B_Cu], self._process_layer),
-                PlotAction("pads-mask", [pcbnew.B_Mask], self._process_mask),
-                PlotAction("silk", [pcbnew.B_SilkS], self._process_layer),
-                PlotAction("outline", [pcbnew.Edge_Cuts], self._process_outline)
-            ]
-        else:
-            to_plot = [
-                PlotAction("board", [pcbnew.Edge_Cuts], self._process_baselayer),
-                PlotAction("clad", [pcbnew.F_Mask], self._process_layer),
-                PlotAction("copper", [pcbnew.F_Cu], self._process_layer),
-                PlotAction("pads", [pcbnew.F_Cu], self._process_layer),
-                PlotAction("pads-mask", [pcbnew.F_Mask], self._process_mask),
-                PlotAction("silk", [pcbnew.F_SilkS], self._process_layer),
-                PlotAction("outline", [pcbnew.Edge_Cuts], self._process_outline)
-            ]
+        for e in ELEMENTS_USED[self.only_mask]:
+            to_plot.append(PlotAction(e, [SUBSTRATE_ELEMENTS[e][plotter.render_back]], SUBSTRATE_PROCESS[e]))
 
         self._container = etree.Element("g", id="substrate")
         self._container.attrib["clip-path"] = "url(#cut-off)"
```

- Fixed the `collect_holes` function to support KiCad 5
  - pad.GetDrillSizeX() and pad.GetDrillSizeY() are KiCad 6 specific, you must use pad.GetDrillSize()
  - KiCad 5 vias were skipped
  - Vias detection crashed on KiCad 5

```diff
diff --git a/kibot/PcbDraw/plot.py b/kibot/PcbDraw/plot.py
index f8990722..17f90185 100644
--- a/kibot/PcbDraw/plot.py
+++ b/kibot/PcbDraw/plot.py
@@ -626,13 +626,15 @@ def collect_holes(board: pcbnew.BOARD) -> List[Hole]:
             continue
         for pad in module.Pads():
             pos = pad.GetPosition()
+            drs = pad.GetDrillSize()
             holes.append(Hole(
                 position=(pos[0], pos[1]),
                 orientation=pad.GetOrientation(),
-                drillsize=(pad.GetDrillSizeX(), pad.GetDrillSizeY())
+                drillsize=(drs.x, drs.y)
             ))
+    via_type = 'VIA' if not isV6(KICAD_VERSION) else 'PCB_VIA'
     for track in board.GetTracks():
-        if not isinstance(track, pcbnew.PCB_VIA) or not isV6(KICAD_VERSION):
+        if track.GetClass() != via_type:
             continue
         pos = track.GetPosition()
         holes.append(Hole(
```

- Changed `pcbnewTransition` to be locally included.
  - Just 2.8 kiB no worth the effort of pulling a dependency

- Replaced `numpy` by a very simple code
  - Currently svgpathtool is disabled, it really needs numpy
  - `numpy` is used to:
    - Multiply matrices (1 line code)
    - Find the index of the smaller element (1 line code)
    - I added a replacemt for the `array` function, it just makes all matrix elements float

- Allow constructing PcbPlotter() using an already loaded board
  - So we don't load it again

- Changed the margin to be a tuple, so the user can control the margins individually

- Added KiCad 6 SVG precision.
  - Fixes issues with Browsers
  - A plotter member controls the precision
  - We adjust the ki2svg and svg2ki converters before plotting
  - This idea was also adopted by upstream and the code adapted to the way the upstream implemented it

### mdrenderer.py

No current changes

### populate.py

- Removed the command line interface, just because it pulls click
- Added `create_renderer`. Just creates the correct MD/HTML mistune renderer
- Made `mdrenderer` import relative. So we get the mdrenderer from the same dir, not the system
- Replicated find_data_file (from plot.py) to avoid cross dependencies

### present.py

This file comes from KiKit, but it has too much in common with `populate.py`.

- Removed `click` import, unused
- Removed the try in boardpage, too broad, doesn't help
- Removed `kikit` import, _renderBoards must be implemented in a different way
- Imported local pybars
- Added source_front, source_back and source_gerbers to the boards.
  So now the images and gerbers come from outside.
- Adapted Template._renderBoards to just copy the files (keeping the extensions)
- Added listResources, with some changes to copyRelativeTo and _copyResources
- The command used for git is now configurable

## 2023-02-14 Update

- Changed to transition 0.3.2 (is a tag, detached from main?!)
- Applied v7 compatibility patches from 9c676a7494995c5aeab086e041bc0ca3967f472d to 6e9c0b7077b5cfed58866f13ad745130e8920185 (2023-01-12)

## 2023-03-01 Update

- Bumped lib footprints (afbab947d981c4583fc6e168c66fc63c31ba6d69)

## 2023-03-20 Various fixes and changes in resistor colors

```diff
diff --git a/kibot/PcbDraw/plot.py b/kibot/PcbDraw/plot.py
index 8ca660e6..9dc45ba9 100644
--- a/kibot/PcbDraw/plot.py
+++ b/kibot/PcbDraw/plot.py
@@ -18,6 +18,7 @@ from . import np
 from .unit import read_resistance
 from lxml import etree, objectify # type: ignore
 from .pcbnew_transition import KICAD_VERSION, isV6, isV7, pcbnew # type: ignore
+from ..gs import GS
 
 T = TypeVar("T")
 Numeric = Union[int, float]
@@ -56,6 +57,8 @@ default_style = {
         7: '#cc00cc',
         8: '#666666',
         9: '#cccccc',
+        -1: '#ffc800',
+        -2: '#d9d9d9',
         '1%': '#805500',
         '2%': '#ff0000',
         '0.5%': '#00cc11',
@@ -64,6 +67,7 @@ default_style = {
         '0.05%': '#666666',
         '5%': '#ffc800',
         '10%': '#d9d9d9',
+        '20%': '#ffe598',
     }
 }
 
@@ -884,10 +888,15 @@ class PlotComponents(PlotInterface):
         try:
             res, tolerance = self._get_resistance_from_value(value)
             power = math.floor(res.log10()) - 1
-            res = Decimal(int(res / 10 ** power))
+            res = str(Decimal(int(res / Decimal(10) ** power)))
+            if power == -3:
+                power += 1
+                res = '0'+res
+            elif power < -3:
+                raise UserWarning(f"Resistor value must be 0.01 or bigger")
             resistor_colors = [
-                self._plotter.get_style("tht-resistor-band-colors", int(str(res)[0])),
-                self._plotter.get_style("tht-resistor-band-colors", int(str(res)[1])),
+                self._plotter.get_style("tht-resistor-band-colors", int(res[0])),
+                self._plotter.get_style("tht-resistor-band-colors", int(res[1])),
                 self._plotter.get_style("tht-resistor-band-colors", int(power)),
                 self._plotter.get_style("tht-resistor-band-colors", tolerance)
             ]
@@ -914,7 +923,7 @@ class PlotComponents(PlotInterface):
             return
 
     def _get_resistance_from_value(self, value: str) -> Tuple[Decimal, str]:
-        res, tolerance = None, "5%"
+        res, tolerance = None, str(GS.global_default_resistor_tolerance)+"%"
         value_l = value.split(" ", maxsplit=1)
         try:
             res = read_resistance(value_l[0])
@@ -1084,6 +1093,12 @@ class PcbPlotter():
             lib = str(footprint.GetFPID().GetLibNickname()).strip()
             name = str(footprint.GetFPID().GetLibItemName()).strip()
             value = footprint.GetValue().strip()
+            if not LEGACY_KICAD:
+                # Look for a tolerance in the properties
+                prop = footprint.GetProperties()
+                tol = next(filter(lambda x: x, map(prop.get, GS.global_field_tolerance)), None)
+                if tol:
+                    value = value+' '+tol
             ref = footprint.GetReference().strip()
             center = footprint.GetPosition()
             orient = math.radians(footprint.GetOrientation().AsDegrees())
```

## 2023-03-27 Fixe for KiCad 7.0.1 polygons

```diff
diff --git a/kibot/PcbDraw/plot.py b/kibot/PcbDraw/plot.py
index 9dc45ba9..8df84469 100644
--- a/kibot/PcbDraw/plot.py
+++ b/kibot/PcbDraw/plot.py
@@ -408,7 +408,22 @@ def get_board_polygon(svg_elements: etree.Element) -> etree.Element:
     for group in svg_elements:
         for svg_element in group:
             if svg_element.tag == "path":
-                elements.append(SvgPathItem(svg_element.attrib["d"]))
+                path = svg_element.attrib["d"]
+                # Check if this is a closed polygon (KiCad 7.0.1+)
+                polygon = re.fullmatch(r"M ((\d+\.\d+),(\d+\.\d+) )+Z", path)
+                if polygon:
+                    # Yes, decompose it in lines
+                    polygon = re.findall(r"(\d+\.\d+),(\d+\.\d+) ", path)
+                    start = polygon[0]
+                    # Close it
+                    polygon.append(polygon[0])
+                    # Add the lines
+                    for end in polygon[1:]:
+                        path = 'M'+start[0]+' '+start[1]+' L'+end[0]+' '+end[1]
+                        elements.append(SvgPathItem(path))
+                        start = end
+                else:
+                    elements.append(SvgPathItem(path))
             elif svg_element.tag == "circle":
                 # Convert circle to path
                 att = svg_element.attrib
```

## 2023-03-30 Removed the tolerance look-up, now using electro_grammar

So now *unit.py* is in charge of returning the tolerance.
Note that we still use a field, but in a very ridiculous way because we add it to the value, to then separate it.

```diff
diff --git a/kibot/PcbDraw/plot.py b/kibot/PcbDraw/plot.py
index 23b7d31f..65fbea66 100644
--- a/kibot/PcbDraw/plot.py
+++ b/kibot/PcbDraw/plot.py
@@ -938,21 +938,20 @@ class PlotComponents(PlotInterface):
             return
 
     def _get_resistance_from_value(self, value: str) -> Tuple[Decimal, str]:
-        res, tolerance = None, str(GS.global_default_resistor_tolerance)+"%"
-        value_l = value.split(" ", maxsplit=1)
+        res, tolerance = None, None
         try:
-            res = read_resistance(value_l[0])
+            res, tolerance = read_resistance(value)
         except ValueError:
-            raise UserWarning(f"Invalid resistor value {value_l[0]}")
-        if len(value_l) > 1:
-            t_string = value_l[1].strip().replace(" ", "")
-            if "%" in t_string:
-                s = self._plotter.get_style("tht-resistor-band-colors")
-                if not isinstance(s, dict):
-                    raise RuntimeError(f"Invalid style specified, tht-resistor-band-colors should be dictionary, got {type(s)}")
-                if t_string.strip() not in s:
-                    raise UserWarning(f"Invalid resistor tolerance {value_l[1]}")
-                tolerance = t_string
+            raise UserWarning(f"Invalid resistor value {value}")
+        if tolerance is None:
+            tolerance = GS.global_default_resistor_tolerance
+        tolerance = str(tolerance)+"%"
+        s = self._plotter.get_style("tht-resistor-band-colors")
+        if not isinstance(s, dict):
+            raise RuntimeError(f"Invalid style specified, tht-resistor-band-colors should be dictionary, got {type(s)}")
+        if tolerance not in s:
+            raise UserWarning(f"Invalid resistor tolerance {tolerance}")
+            tolerance = "5%"
         return res, tolerance
 
 
@@ -1113,7 +1112,7 @@ class PcbPlotter():
                 prop = footprint.GetProperties()
                 tol = next(filter(lambda x: x, map(prop.get, GS.global_field_tolerance)), None)
                 if tol:
-                    value = value+' '+tol
+                    value = value+' '+tol.strip()
             ref = footprint.GetReference().strip()
             center = footprint.GetPosition()
             orient = math.radians(footprint.GetOrientation().AsDegrees())
diff --git a/kibot/PcbDraw/unit.py b/kibot/PcbDraw/unit.py
index 2fad683c..0c5dfcab 100644
--- a/kibot/PcbDraw/unit.py
+++ b/kibot/PcbDraw/unit.py
@@ -1,10 +1,9 @@
 # Author: Salvador E. Tropea
 # License: MIT
-from decimal import Decimal
 from ..bom.units import comp_match
 
 
-def read_resistance(value: str) -> Decimal:
+def read_resistance(value: str):
     """
     Given a string, try to parse resistance and return it as Ohms (Decimal)
 
@@ -13,5 +12,4 @@ def read_resistance(value: str) -> Decimal:
     res = comp_match(value, 'R')
     if res is None:
         raise ValueError(f"Cannot parse '{value}' to resistance")
-    v, mul, uni = res
-    return Decimal(str(v))*Decimal(str(mul[0]))
+    return res.get_decimal(), res.get_extra('tolerance')
```
