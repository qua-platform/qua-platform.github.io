import pytest

from qm.exceptions import QmValueError


def test_set_io1_values(mock_qm):
    mock_qm.set_io1_value(1)
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [1, None])
    mock_qm.set_io1_value(1.1)
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [1.1, None])
    mock_qm.set_io1_value(True)
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [True, None])

    mock_qm._frontend.set_io_values.reset_mock()

    mock_qm.io1 = 1
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [1, None])
    mock_qm.io1 = 1.1
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [1.1, None])
    mock_qm.io1 = True
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [True, None])


def test_io1_invalid_values(mock_qm):
    with pytest.raises(QmValueError):
        mock_qm.set_io1_value([1, 1, 1])

    with pytest.raises(QmValueError):
        mock_qm.io1 = [1, 1, 1]


def test_set_io2_values(mock_qm):
    mock_qm.set_io2_value(1)
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [None, 1])
    mock_qm.set_io2_value(1.1)
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [None, 1.1])
    mock_qm.set_io2_value(True)
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [None, True])

    mock_qm._frontend.set_io_values.reset_mock()

    mock_qm.io2 = 1
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [None, 1])
    mock_qm.io2 = 1.1
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [None, 1.1])
    mock_qm.io2 = True
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [None, True])


def test_io2_invalid_values(mock_qm):
    with pytest.raises(QmValueError):
        mock_qm.set_io2_value([1, 1, 1])

    with pytest.raises(QmValueError):
        mock_qm.io2 = [1, 1, 1]


def test_set_io_values(mock_qm):
    mock_qm.set_io_values(1, -1)
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [1, -1])
    mock_qm.set_io_values(1.1, -1.1)
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [1.1, -1.1])
    mock_qm.set_io_values(True, False)
    mock_qm._frontend.set_io_values.assert_called_with('qm-1', [True, False])


def test_set_io_invalid_values(mock_qm):
    with pytest.raises(QmValueError):
        mock_qm.set_io_values([1, 2, 3], [1, 2, 3])

    with pytest.raises(QmValueError):
        mock_qm.set_io_values([1, 2, 3], 1)

    with pytest.raises(QmValueError):
        mock_qm.set_io_values(1, [1, 2, 3])
