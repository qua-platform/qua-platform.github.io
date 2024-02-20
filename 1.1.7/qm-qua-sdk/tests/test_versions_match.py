from pathlib import Path
import re


def get_version_from_toml():
    version_regex = re.compile(r"\s*version\s*=\s*[\"']\s*([-+.\w]{3,})\s*[\"']\s*")
    dir_path = Path(__file__).parent.parent
    dir_path /= "pyproject.toml"
    with dir_path.open(mode="r") as f:
        for line in f:
            match = version_regex.search(line)
            if match is not None:
                return match.group(1).strip()
    return ""


def test_version_match():
    import qm.version

    toml_version = get_version_from_toml()
    assert toml_version == qm.version.__version__
