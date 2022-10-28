# Populate

Populate allows you to write a simple population guide for you board in markdown
and automatically convert to either a webpage with images or a markdown files
with images suitable for GitHub wiki.

It allows you to write text, incrementally add new components to the board and
highlight newly added components.

The core code for this tool comes from the [PcbDraw project](https://github.com/yaqwsx/PcbDraw/).
This documentation is adapted from the original project.


## Usage

You must define a `populate` type output, and this output must indicate how to
draw the steps using a `pcbdraw` type output. The name of the output using to
draw is indicated in the `renderer` option. So you need to define at least
two outputs, i.e.:

```yaml
kiplot:
  version: 1

outputs:
  - name: PcbDraw
    comment: "How to draw a step"
    type: pcbdraw
    run_by_default: false
    options:
      format: png

  - name: Populate
    comment: "Populate example"
    type: populate
    dir: Populate
    options:
      renderer: PcbDraw
      input: tests/data/plain_html.md
```

When using the `populate` command from the `pcbdraw` project all the options
to render the images is contained in the input markdown file
(`tests/data/plain_html.md` in the above example). When using KiBot all the
information comes from the KiBot configuration file, and the YAML text from
the input markdown file is discarded.


## Source file format

The source file format is a simple markdown file with two specialties -- each
list item is considered as a single step in populating and will generate an
image. The content of the item is the step description. See
[example](../tests/data/plain_html.md).

To specify which side of the board and which components to add and highlight start the item with a clause in form:

```
- [[<front|back> | <comma separated list of components to add> ]]
```

For example:

- `[[front | R1,R2 ]]` will render front side of the board and adds R1 and R2.
- `[[back | ]]` will render the back side and no components will be added


## Handlebars template

To specify HTML output you can use a [Handlebar](https://handlebarsjs.com/)
template. The template is fed with a data structure like this:

```{.json}
{
    "items": [
        {
            "type": "comment",
            "is_comment": true,
            "content": "Generated HTML from markdown of the comment"
        },
        {
            "type": "step",
            "is_step": true,
            "steps": [
                {
                    "img": "path to generated image",
                    "comment": "Generated HTML from markdown of the comment"
                }
            ]
        }
    ]
}
```

There can be multiple `step` and `comment` sections.
