from typing import TypeVar, List

import pytest

from qm.grpc.qua_config import QuaConfigIntegrationWeightSample
from qm.program._qua_config_to_pb import build_iw_sample
from qm.utils.list_compression_utils import split_list_to_chunks

T = TypeVar('T')

@pytest.mark.parametrize(
    "input_list,expected_output",
    [
        ([1, 2, 3, 4, 5, 6, 7, 8, 9], [[1, 2, 3, 4, 5, 6, 7, 8, 9]]),
        ([1], [[1]]),
        (["s"] * 3, [["s"] * 3]),
        ([1, 2, 1, 1, 1, 2, 1], [[1, 2], [1, 1, 1], [2, 1]]),
        ([1, 2, 1, 2, 1], [[1, 2, 1, 2, 1]]),
        ([1, 2, 3] * 3, [[1, 2, 3] * 3]),
        ([(1, 2)] * 2 + [3] * 4 + ["u"] * 5, [[(1, 2)] * 2, [3] * 4, ["u"] * 5]),
        ([1, 1, 1, 1, 1, 2], [[1] * 5, [2]]),
        ([2, 1, 1, 1, 1, 1], [[2], [1] * 5]),
    ],
)
def test_split_list_to_chunks(input_list: List[T], expected_output: List[List[T]]):
    chunks = split_list_to_chunks(input_list)
    assert [c.data for c in chunks] == expected_output


@pytest.mark.parametrize(
    "inputs,expected_output",
    [
        ([0.0, 1.0, 2.0, 3.0], [QuaConfigIntegrationWeightSample(value=s*1.0, length=4) for s in range(4)]),
        ([1.0, 1.0, 1.0, 1.0, 1.0], [QuaConfigIntegrationWeightSample(value=1.0, length=20)]),
        ([1.0] * 13, [QuaConfigIntegrationWeightSample(value=1.0, length=4*13)]),
        ([1.0], [QuaConfigIntegrationWeightSample(value=1.0, length=4)]),
        ((1.0, 12), [QuaConfigIntegrationWeightSample(value=1.0, length=12)]),
        ([(1.0, 12)], [QuaConfigIntegrationWeightSample(value=1.0, length=12)]),
        ([(0.0, 4), (2.0, 12), (1.0, 8)], [
            QuaConfigIntegrationWeightSample(value=0.0, length=4),
            QuaConfigIntegrationWeightSample(value=2.0, length=12),
            QuaConfigIntegrationWeightSample(value=1.0, length=8),
        ]),
    ],
)
def test_build_iw_sample(inputs, expected_output: List[QuaConfigIntegrationWeightSample]):
    output = build_iw_sample(inputs)
    assert output == expected_output
