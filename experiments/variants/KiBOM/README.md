# KiBOM variants

This is an analysis and test of the *variants* implementation of [KiBOM](https://github.com/SchrodingersGat/KiBoM)

## What goes inside the SCH

- The variants are implemented using the `Config` field (the name can be configured).
- By default a component is included in all variants.
- You can exclude a component from one variant adding `-VARIANT_NAME` to the `Config`.
  - If you want to exclude this component from more than one variant just add more `-VARIANT_NAME` entries. Comma separated.
- If a component will be included **only** in one variant you can use `+VARIANT_NAME`.
  - Again you can add more than one `+VARIANT_NAME` entry. So the component will be included only if generating one of the selected variants.

## What goes outside the SCH

- When you generate the BoM you can select one or more variants, again comma separated.
- The `-VARIANT_NAME` and `+VARIANT_NAME` is tested using a list of all the indicated variants.
- By default the list of variants is ['default']. So *default* is like a special variant.

## Where is in the code?

The Component.isFitted() method implements the functionality.

## Conclusion

### Advantages

- Almost all the information is inside the project.
- You have "exclude from" and "include only" options.

### Disadvantages

- The `Config` field could become large.




