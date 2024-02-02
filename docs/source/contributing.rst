.. index::
   single: contributing

Contributing
------------

If you find KiBot useful please consider contributing to the project.
There various ways to contribute. Of course donations are welcome
(`donate <https://www.paypal.com/donate/?hosted_button_id=K2T86GDTTMRPL>`__),
but there are other ways to contribute:

-  In general:

   -  Your workflow: What’s missing in KiBot for your workflow? Comment
      it in the
      `discussions <https://github.com/INTI-CMNB/KiBot/discussions/categories/missing-in-my-workflow>`__
   -  Configuration for a manufacturer: If you have a configuration
      known to work for a manufacturer please consider contributing it.
      Even if this is a small manufacurer, this helps to know what are
      the most common options.
   -  Mention KiBot: If your project or company uses KiBot you can
      mention it, so people know about KiBot. Also if you are reporting
      a KiCad issue, currently KiCad developers doesn’t pay much
      attention to automation details.

-  If you are a Windows/Mac OS X user:

   -  If you managed to run it locally consider contributing a tutorial
      of how to do it.
   -  If you run KiBot on CI/CD and want to run it locally: consider
      investing some time on tests. Just comment in the
      `discussions <https://github.com/INTI-CMNB/KiBot/discussions/categories/other-platforms>`__
      and I’ll help you to run tests to adapt the code. Now that KiCad 6
      uses Python 3 most of KiBot functionality should work on Windows
      and Mac OS X. People are using WSL to run KiBot, but we don’t have
      a tutorial about how to do it.

-  If you use a Linux that isn’t derived from Debian:

   -  Consider helping to add better support for it. Do you know the
      name of the packages for the dependencies? Do you know how to
      create a package for your distro?

-  If you are good writing tutorials:

   -  Consider writing some tutorial about using KiBot. Some examples:

      -  How to start using it
      -  How to use filters/variants
      -  How to create good BoMs

-  If you know Python:

   -  Create a new output: KiBot is modular, creating a new output can
      be done just using some of the ``kibot/out_*`` files as template.
      The outputs works as plugins and they are automatically discovered
      by KiBot. Note that you can add them to
      ``~/.config/kibot/plugins``
   -  Add regression tests: If you know about Python testing you can add
      tests to ``tests/test_plot/``. We try to cover 100% of the code.
      Even simple tests that check the code executes are welcome.

-  If you know HTML/CSS:

   -  Internal BoM styles: You can just take a look at the generated
      HTMLs and contribute a CSS, or take a look at the code
      (``kibot/bom/html_writer.py``) and add more functionality.
   -  Navigate results styles: Similar to the above but for the
      ``navigate_results`` output (``kibot/out_navigate_results.py``).

-  If you have drawing skills:

   -  Navigate results icons: Currently we have only one set of icons,
      they are from KiCad 6. Alternative icons are welcome.

