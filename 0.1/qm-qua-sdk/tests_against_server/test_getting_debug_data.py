from qm.quantum_machines_manager import QuantumMachinesManager


def test_open_qmm_without_debug_data_works(host_port, server_credentials):
    qmm = QuantumMachinesManager(**host_port)
    assert qmm._debug_data is None


def test_open_qmm_with_debug_data_works(host_port, server_credentials):
    qmm = QuantumMachinesManager(**host_port, add_debug_data=True)
    debug_data = qmm._debug_data
    assert debug_data is not None
    # upon init qmm tries the server with 3 grpc calls: get_version, get_info, healthcheck
    assert len(debug_data.received_headers) == 3
