# IBoM variants

This is an analysis and test of the *variants* implementation of [IBoM](https://github.com/openscopeproject/InteractiveHtmlBom)

## What goes inside the SCH

- The field used for variants must be specified using `--variant-field`
- The field can contain only one value. So you create some kind of component groups.

## What goes outside the SCH

- Two optional lists are passed to create the variant.
- Components without a group are always included.
- Whitelist: only the groups listed here are included.
  - If this list is empty all groups are included, unless listed in the blacklist.
- Blacklist: groups listed here are excluded.

## Where is in the code?

In core/ibom.py function skip_component.

## Conclusion

### Advantages

- The `Config` field is simple.
- You have "exclude from" and "include only" options.

### Disadvantages

- Critical part of the information is outside the project.




