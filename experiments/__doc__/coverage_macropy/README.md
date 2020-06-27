# Coverage and macropy

When using the `with` macro block [Coverage.py](https://coverage.readthedocs.io/en/coverage-5.1/) fails to detect some sentences.

Here is a small example to show it. The `mymacros.py` contains a macro that was reduced to *do nothing*.

Running `make` you can see how 3 lines in `application.py` are marked as uncovered.

I commented these lines in the code with `# <--- Not covered?`

The coverage version used is the Debian stable one:

```
Coverage.py, version 4.5.2 with C extension
Documentation at https://coverage.readthedocs.io
```

I also tried the code from GitHub (installed on my user:

```
Coverage.py, version 5.1.1a0 with C extension
Full documentation is at https://coverage.readthedocs.io/en/coverage-5.1.1a0
```
