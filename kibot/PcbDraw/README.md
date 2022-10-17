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

### convert.py

- Made the `pcbdraw` import relative

### convert_common.py

No current changes

### convert_unix.py

- Made the `pcbdraw` import relative

### convert_windows.py

- Made the `pcbdraw` import relative

### unit.py

No current changes

### plot.py

- Made the `pcbdraw` import relative
- Disabled `shrink_svg`
  - Changes the old behavior, so this should be optional
  - Pulls a problematic dependency: svgpathtool
- Changed calls to `ComputeBoundingBox()` to use `aBoardEdgesOnly=True`
  - To get the same behavior as 0.9.0-5
  - This changes the size of the SVG to the size of the board
  - `shrink_svg` must be disabled or it reverts the size to the detected
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
