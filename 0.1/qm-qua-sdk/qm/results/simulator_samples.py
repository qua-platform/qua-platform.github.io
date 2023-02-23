import numpy as np


class SimulatorSamples:
    def __init__(self, controllers):
        for k, v in controllers.items():
            self.__setattr__(k, v)

    @staticmethod
    def from_np_array(arr: np.ndarray):
        controllers = dict()
        for col in arr.dtype.names:
            parts = col.split(":")
            controller = controllers.setdefault(
                parts[0], {"analog": dict(), "digital": dict()}
            )
            controller[parts[1]][parts[2]] = arr[col]
        res = dict()
        for item in controllers.items():
            res[item[0]] = SimulatorControllerSamples(
                item[1]["analog"], item[1]["digital"]
            )
        return SimulatorSamples(res)


class SimulatorControllerSamples(object):
    def __init__(self, analog, digital):
        self.analog = self._add_keys_for_first_con(analog)
        self.digital = self._add_keys_for_first_con(digital)
        self._analog_conns = analog
        self._digital_conns = digital

    @staticmethod
    def _add_keys_for_first_con(data):
        first_con_data = {k[2:]: v for (k, v) in data.items() if k.startswith("1-")}
        return {**data, **first_con_data}

    def plot(self, analog_ports=None, digital_ports=None):
        """Plots the simulated output of the OPX in the given ports.
        If no ports are given, all active ports are plotted.

        Args:
            analog_ports: Union[None, str, list[str]]
            digital_ports: Union[None, str, list[str]]
        """
        import matplotlib.pyplot as plt

        for port, samples in self._analog_conns.items():
            if analog_ports is None or port in analog_ports:
                plt.plot(samples, label=f"Analog {port}")
        for port, samples in self._digital_conns.items():
            if digital_ports is None or port in digital_ports:
                plt.plot(samples, label=f"Digital {port}")
        plt.xlabel("Time [ns]")
        plt.ylabel("Output")
        plt.legend()
