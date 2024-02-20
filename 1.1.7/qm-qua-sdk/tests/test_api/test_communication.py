import pytest

from qm.communication.http_redirection import parse_octaves
from qm.exceptions import QmLocationParsingError


@pytest.mark.parametrize("response", ["", ";", ";;", ";;;"])
def test_parse_octaves_valid_no_octaves_response(response: str):
    octaves = parse_octaves(response)
    assert octaves == {}


@pytest.mark.parametrize("response", [";octave1,host1:1234", "octave1,host1:1234;", ";octave1,host1:1234;"])
def test_parse_octaves_valid_one_octave_response(response: str):
    octaves = parse_octaves(response)
    assert octaves == {"octave1": ("host1", 1234)}


@pytest.mark.parametrize("response",
                         ["octave1,host1:1234;octave2,host2:1234"
                          ";octave1,host1:1234;octave2,host2:1234",
                          "octave1,host1:1234;octave2,host2:1234;",
                          ";octave1,host1:1234;octave2,host2:1234;"])
def test_parse_octaves_valid_two_octaves_response(response: str):
    octaves = parse_octaves(response)
    assert octaves == {"octave1": ("host1", 1234), "octave2": ("host2", 1234)}

@pytest.mark.parametrize("response", [
    "no_comma;host1:1234;octave2,host2:1234",
    "no_port,host1:;octave2,host2:1234",
    "no_host,:1234;octave2,host2:1234",
    "no_octave_name,host:1234;:1234",
    "no_second_host,host:1234;octave,:1234",
    "no_second_port,host:1234;octave2,host2:",
])
def test_parse_octaves_invalid_response(response: str):
    with pytest.raises(QmLocationParsingError):
        parse_octaves(response)
