# APPLES
Automatic Python Plugin Loading &amp; Executing Script

This is meant to be a moddable framework, where adding in functionality is as simple as copying a folder or two. There are also several pre-built plugins for useful things like command line interfaces.

The 0.2.0 Refactor is incompatible with older versions of APPLES as it uses a different folder structure. It does offer some advantages though.

+ A clearer plugin manifest format. (JSON based, includes "format" attribute for supporting multiple format types)
+ Simpler plugins. (no `__register__` function)
+ Better separation between plugins. (plugins are placed in the plugins folder, instead of cluttering up the root APPLES directory)
+ Better import logic. (plugins are put in the correct module/submodule)
+ Better import directives. (import directives are clearer and more versatile)
+ Better command input processing. (shlex.split instead of custom command splitting)
+ Better command adding. (command decorator instead of add_command))
+ Sub-module usage. (use of __init__.py instead of apples.py making it easier to add as a sub-module to another program when necessary)
+ Better built in logging. (use of logging instead of print)
+ Command line logging enable. (Turn on logging for the entire program)

The following features from 0.1.4 will not be ported over.
+ Auto updating (manual updates are available however)
