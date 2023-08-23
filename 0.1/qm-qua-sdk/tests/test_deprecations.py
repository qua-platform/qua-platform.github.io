import pathlib
import re

import packaging.version
from qm.version import __version__


def test_no_outdated_functions_exists_in_code():
    """Finds all outdated deprecations in the code according to the version.
    Fails on outdated deprecation
    """
    curr_version = packaging.version.parse(__version__)
    print(f"current version: {__version__} ({curr_version})")
    found_deprecations = []

    root_directory = pathlib.Path("../qm")
    for path_object in root_directory.rglob('*'):
        if path_object.is_file() and path_object.suffix == ".py":
            with path_object.open("r") as file_object:
                matches = re.findall(
                    '@deprecated[(]"(?P<version>[0-9.]*)", "(?P<removed_in>[0-9.]*)", details="(?P<details>[^,]*)"[)].*\n[ \t]*def (?P<func_name>[^(]*)',
                    file_object.read()
                )
                if matches:
                    found_deprecations += [(*match, path_object.name) for match in
                                           matches]

    found_outdated_deprecation = False
    for version, last_version, reason, func_name, file_name in found_deprecations:
        last_version = packaging.version.parse(last_version)
        if last_version <= curr_version:
            print(f"{file_name}: outdated deprecation: '{func_name}' "
                  f"removed in version: {last_version}")
            found_outdated_deprecation = True

    assert not found_outdated_deprecation
