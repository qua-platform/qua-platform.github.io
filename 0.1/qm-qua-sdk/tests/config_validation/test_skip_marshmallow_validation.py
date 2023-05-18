import pytest
from ..serialization.sample_config import config

from qm.program._qua_config_to_pb import load_config_pb
from qm.program import load_config


def test_check_protobuf_message():
    scheme = load_config(config)
    pb = load_config_pb(config)
    assert scheme.to_dict() == pb.to_dict()
