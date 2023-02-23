import numpy as np

from qm.grpc.quantum_simulator.v1 import (
    Qubit,
    CapacitiveCoupler,
    Resonator,
    QubitProperties,
    IQMixerIn,
    FixedFrequencyQubit,
    InputPort,
    OutputPort,
    AnalogFrontend,
    PhysicalConfig,
    QubitResonatorCoupling,
    ReadoutResonator,
    IQMixerOut,
    QubitQubitCoupling,
)

physical_config1 = PhysicalConfig(
    qubits={
        "QB1": Qubit(
            properties=QubitProperties(
                frequency=2.0 * np.pi * 5.8,
                anharmonicity=-2.0 * np.pi * 200 * 1e-3,
                t1=np.inf,
                t2=np.inf,
            ),
            i_q_mixer=IQMixerIn(
                lo_frequency=2.0 * np.pi * 5.7,
                i=InputPort(controller="con1", id=1),
                q=InputPort(controller="con1", id=2),
            ),
            analog_frontend=AnalogFrontend(amp_factor=1.0),
            fixed_frequency_qubit=FixedFrequencyQubit(),
        ),
    },
)

physical_config2 = PhysicalConfig(
    qubits={
        "QB1": Qubit(
            properties=QubitProperties(
                frequency=2.0 * np.pi * 5.8,
                anharmonicity=-2.0 * np.pi * 200 * 1e-3,
                t1=np.inf,
                t2=np.inf,
            ),
            i_q_mixer=IQMixerIn(
                lo_frequency=2.0 * np.pi * 5.7,
                i=InputPort(controller="con1", id=1),
                q=InputPort(controller="con1", id=2),
            ),
            analog_frontend=AnalogFrontend(amp_factor=1.0),
            fixed_frequency_qubit=FixedFrequencyQubit(),
        ),
    },
    resonators={
        "RES": Resonator(
            frequency=2.0 * np.pi * 6.0,
            i_q_mixer=IQMixerIn(
                lo_frequency=2.0 * np.pi * 5.7,
                i=InputPort(controller="con1", id=3),
                q=InputPort(controller="con1", id=4),
            ),
            analog_frontend=AnalogFrontend(amp_factor=1.0),
            readout_resonator=ReadoutResonator(
                i_q_mixer=IQMixerOut(
                    i=OutputPort(controller="con1", id=1),
                    q=OutputPort(controller="con1", id=2),
                    lo_frequency=2.0 * np.pi * 5.7,
                )
            ),
        ),
    },
    qubit_resonator_coupling=[
        QubitResonatorCoupling(qubit="QB1", resonator="RES", g=1.0)
    ],
)

physical_config3 = PhysicalConfig(
    qubits={
        "QB1": Qubit(
            properties=QubitProperties(
                frequency=2.0 * np.pi * 5.8,
                anharmonicity=-2.0 * np.pi * 200 * 1e-3,
                t1=np.inf,
                t2=np.inf,
            ),
            i_q_mixer=IQMixerIn(
                lo_frequency=2.0 * np.pi * 5.7,
                i=InputPort(controller="con1", id=1),
                q=InputPort(controller="con1", id=2),
            ),
            analog_frontend=AnalogFrontend(amp_factor=1.0),
            fixed_frequency_qubit=FixedFrequencyQubit(),
        ),
        "QB2": Qubit(
            properties=QubitProperties(
                frequency=2.0 * np.pi * 5.8,
                anharmonicity=-2.0 * np.pi * 200 * 1e-3,
                t1=np.inf,
                t2=np.inf,
            ),
            i_q_mixer=IQMixerIn(
                lo_frequency=2.0 * np.pi * 5.7,
                i=InputPort(controller="con1", id=3),
                q=InputPort(controller="con1", id=4),
            ),
            analog_frontend=AnalogFrontend(amp_factor=1.0),
            fixed_frequency_qubit=FixedFrequencyQubit(),
        ),
    },
    capacitive_couplers={
        "CAP": CapacitiveCoupler(g=InputPort(controller="con1", id=5), amp_factor=1.0)
    },
    qubit_qubit_coupling=[
        QubitQubitCoupling(qb1="QB1", qb2="QB2", capacitive_coupler="CAP")
    ],
)
