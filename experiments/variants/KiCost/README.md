# KiCost variants (modern style)

This is an analysis and test of the *variants* implementation of [KiCost](https://github.com/xesscorp/KiCost)
An old style used `kicost.VARIANT:FIELD` to assign fields. So you could define `kicost.V1:DNP`.

## What goes inside the SCH

- The variants are implemented using the `variant` field (`version` is an alias).
- The `variant` field can contain more than one value, valid separators are: comma `,`, semicolon `;`, slash `/` and space ` `.
  Note: spaces are removed, and a vanriant tag can't contain spaces because this is a separator. (`re.split('[,;/ ]', variants)`)
- Components without a variant are always included.
- Components with one or more variants are included only if requested (`--variant REGEX` matches any of the listed variants)

## What goes outside the SCH

- When you generate the spreadsheet you can select one or more variants using a regex (`--variant REGEX`).
- Components containing one or more variants that match the regex are added.
- No exclusion mechanism is available.
- `REGEX` isn't case sensitive.

## Where is in the code?

Source `kicost/edas/tools.py` function `remove_dnp_parts(components, variant)`.
The old mechanism is part of `kicost/edas/eda_kicad.py` function `extract_fields(part, variant)` combined with the above code.

## Conclusion

### Advantages

- Most of the information is inside the project.
- A regex allows pattern matching.

### Disadvantages

- You only have an "include only" option.
- The regex could become complex.

## Old mechanism

KiCost has a field rename mechanism. Fields named `kicost.VARIANT:FIELD` are:

- Renamed to `FIELD` if `VARIANT` matches `--variant REGEX`
- Discarded otherwise

This can be used with the DNP mechanism:

- The name of the field is `dnp` or `nopop` (case insensitive)
- If it contains anything other than 0 (evaluated as float) the component is removed.
