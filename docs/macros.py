"""
Basic example of a Mkdocs-macros module
"""

import math

def define_env(env):
    """
    This is the hook for defining variables, macros and filters

    - variables: the dictionary that contains the environment variables
    - macro: a decorator function, to declare a macro.
    - filter: a function with one of more arguments,
        used to perform a transformation
    """

    env.variables["discord"] = "[![discord](https://img.shields.io/discord/806244683403100171?label=QUA&logo=Discord&style=plastic)](https://discord.gg/7FfhhpswbP)"

    @env.macro
    def requirement(name, version_string = None):
        if name == "OPX" or (name=="QOP" and version_string is not None and version_string.split(".")[0]=="1"):
            return  f"[![{name}](https://img.shields.io/badge/OPX-{version_string}-blue){{ .middle }}](https://qm-docs.qualang.io/about_doc.html#shields){{ .middle }}"
        elif name == "OPX+" or name == "QOP":
            return  f"[![{name}](https://img.shields.io/badge/OPX+-{version_string}-blue){{ .middle }}](https://qm-docs.qualang.io/about_doc.html#shields){{ .middle }}"
        elif name == "Octave" or name == "OPT":
            return  f"[![{name}](https://img.shields.io/badge/Add_on-{name}-orange){{ .middle }}](https://qm-docs.qualang.io/about_doc.html#shields){{ .middle }}"
        elif name == "QUA":
            return  f"[![QUA](https://img.shields.io/badge/QUA-{version_string}-green){{ .middle }}](https://qm-docs.qualang.io/about_doc.html#shields){{ .middle }}"
        else:
            raise ValueError(f"Unknown requirement: {name}")

    @env.macro
    def f(api_path:str):
        root = api_path.split(".")[-1]
        return f"[`{root}()`][{api_path}]"

    # GENERAL DOCUMENTATION

    # add to the dictionary of variables available to markdown pages:
    # env.variables['baz'] = "John Doe"

    # NOTE: you may also treat env.variables as a namespace,
    #       with the dot notation:
    # env.variables.baz = "John Doe"

    # @env.macro
    # def bar(x):
    #     return (2.3 * x) + 7

    # If you wish, you can  declare a macro with a different name:
    # def f(x):
    #     return x * x
    # env.macro(f, 'barbaz')

    # or to export some predefined function
    # env.macro(math.floor) # will be exported as 'floor'


    # create a jinja2 filter
    # @env.filter
    # def reverse(x):
    #     "Reverse a string (and uppercase)"
    #     return x.upper()[::-1]