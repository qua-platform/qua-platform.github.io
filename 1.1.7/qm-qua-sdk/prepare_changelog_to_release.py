import os
import sys
import datetime

WORKING_DIR = os.path.dirname(__file__)
SOURCE_FILE = os.path.join(WORKING_DIR, "CHANGELOG.md")
TARGET_FILE = os.path.join(WORKING_DIR, "docs", "Releases", "qm_qua_releases.md")


def _save(source: str, filename: str) -> None:
    with open(filename, "w") as f:
        f.write(source)


def _load(filename: str) -> str:
    with open(filename, "r") as f:
        return f.read()


def _modify_line(line: str) -> str:
    if line.startswith("## Unreleased"):
        return ""
    if line.startswith("### "):
        line = line.strip("# ")
        return f"\n**{line}**\n"
    if line.startswith("## "):
        return "\n" + line
    for word in [":page_with_curl: ", ":guardswoman: "]:
        if word in line:
            return line.replace(word, "")
    return line


def _reformat_changelog(source: str) -> str:
    lines = source.split("\n")
    lines[0] = "# Python Package (qm-qua) Releases\n"
    modified_lines = [_modify_line(line) for line in lines if line.strip()]
    modified_lines[1] += "\n"
    modified_lines[-1] += "\n"
    return "\n".join(modified_lines)


def _change_unreleased_to_version(text: str, release_version) -> str:
    today = datetime.date.today().strftime("%Y-%m-%d")
    return text.replace("## Unreleased", f"## Unreleased\n\n\n## {release_version} - {today}")


def prepare_change_log_to_release(release_version: str) -> None:
    source = _load(SOURCE_FILE)
    release_text = _change_unreleased_to_version(source, release_version)
    reformatted_text = _reformat_changelog(release_text)
    _save(release_text, SOURCE_FILE)
    _save(reformatted_text, TARGET_FILE)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("You should enter the parameter for the release version.")
        sys.exit(1)

    input_parameter = sys.argv[1]
    prepare_change_log_to_release(input_parameter)
