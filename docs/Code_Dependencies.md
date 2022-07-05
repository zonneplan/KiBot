# Code Dependencies

This document is about how the outputs and preflights declare their dependencies.
Is intended for developers trying to understand how to create plug-ins.

The dependencies are declared as YAML inside the docstring of the module.
So they look like some kind of comment.

The YAML code must contain a key named `Dependencies` with a list of dependencies.

The `dep_dowloader.py` module contains the core dependencies.

There are two type of dependencies:

1. Actual dependencies, they contain a `role`
2. Template dependencies, they are referenced by other dependencies using `from`

An example of template:

```yaml
  - name: KiCad Automation tools
    github: INTI-CMNB/KiAuto
    command: pcbnew_do
    pypi: kiauto
    downloader: pytool
    id: KiAuto
```

And an example of dependency that uses a template:

```yaml
  - from: KiAuto
    role: mandatory
    version: 1.6.7
```

The `name` is the name shown to the user, the `id` is the internal name.

Here are the most common attributes:

- `role`: What this dependency is used for. The `mandatory` role means this dependency must be met in order to run the plug-in.
- `command`: Name of the executable.
- `version`: The minimum version needed.
- `github`: The name of the GitHub project hosting it. Useful for tools that can be downloaded using the `python` downloader.
- `url`: When page for the tool. The one to visit.
- `url_down`: The URL to download the tool. Useful for the downloaders.
- `debian`: The name of the Debian package for this dependency.
- `extra_deb`: Extra Debian packages needed for this tool. They are usually suggested dependencies that are needed for our use.
- `python_module`: `true` when this tool provides a Python module (and no executable). Something we `import`.
- `module_name`: The name of the Python module. By default we assume this is the same as the `name`.
- `plugin_dirs`: Used for tools that can be installed as a KiCad plug-in. Is a list of directories where the plug-in can be found, they are relative to the KiCad plug-in places.
- `help_option`: Used when the tool doesn't implement `--version`.
- `no_cmd_line_version_old`: `true` when old versions of the tool doesn't implement `--version`.
- `pypi`: Name of the tool in PyPi.org
- `downloader`: The name of a Python function declared in `dep_downloader.py` that can be used to download the tool.
- `comments`: A string or a list of strings containing extra information to show to the user when the tool isn't installed.

Currently we have the following downloaders:

- `pytool`: Can download a Python module from GitHub. After downloading the sources of the last release we run `pip install -U .`
- `python`: Used to install stuff from PyPi. We just run `pip install -U PYPI_NAME`
- `git`: Installs Git
- `convert`: Installs ImageMagick
- `gs`: Installs Ghostscript
- `rsvg`: Installs the binary tools from the RSVG library
- `rar`: Installs RAR

Most downloaders are very limited and poorly tested. They are just a last resort.
