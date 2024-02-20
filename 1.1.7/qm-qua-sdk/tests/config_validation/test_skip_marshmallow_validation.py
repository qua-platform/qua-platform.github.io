import pytest

from qm import DictQuaConfig
from ..serialization.sample_config import config, opx1000_config

from qm.program._qua_config_to_pb import load_config_pb
from qm.program import load_config


@pytest.mark.parametrize("config_instance", [config, opx1000_config])
def test_check_protobuf_message(config_instance: DictQuaConfig):
    scheme = load_config(config_instance)
    pb = load_config_pb(config_instance)
    assert scheme.to_dict() == pb.to_dict()
