# Coverage and mcpyrate

This example implements the correct solution.

- We must ensure all the new nodes has the proper line info.
  - `mcpyrate` can fill it, but will be the line number for the `with` statement.
  - We recycle the Str node and copy the line info to the newly created nodes.
- Lines with just an Exp are optimized out and never show coverage.
