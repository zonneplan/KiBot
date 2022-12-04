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
