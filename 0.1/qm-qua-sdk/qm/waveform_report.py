import base64
import dataclasses
import datetime
import functools
import logging
import os.path

from typing import Dict, List, Optional, Any, Union, Tuple, Iterable
from abc import abstractmethod
from abc import ABCMeta
from dataclasses import dataclass

import numpy as np
import plotly.colors
import plotly.graph_objects as go


@dataclass(frozen=True)
class PlayedWaveform(metaclass=ABCMeta):
    waveform_name: str
    pulse_name: str
    length: int
    timestamp: int
    iq_info: Dict[str, Any]
    element: str
    output_ports: List[int]
    controller: str
    pulser: Dict[str, Any]

    @classmethod
    def from_job_dict(cls, dict_description: Dict, formated_attribute_dict: Dict):
        formated_attribute_dict.update(
            pulse_name=dict_description["pulseName"],
            waveform_name=dict_description["waveformName"],
            timestamp=int(dict_description["timestamp"]),
            length=int(dict_description["length"]),
            iq_info=dict_description["iqInfo"],
            element=dict_description["quantumElements"],
            output_ports=[int(p) for p in dict_description["outputPorts"]],
            pulser=dict_description["pulser"],
            controller=dict_description["pulser"]["controllerName"],
        )
        return cls(**formated_attribute_dict)

    @property
    def ports(self) -> List[int]:
        return self.output_ports

    @property
    def is_iq(self) -> bool:
        return self.iq_info["isPartOfIq"]

    @property
    def is_I_pulse(self) -> bool:
        return self.iq_info["isI"]

    @property
    def get_iq_association(self) -> str:
        if not self.is_iq:
            return ""
        return "I" if self.is_I_pulse else "Q"

    @property
    def ends_at(self) -> int:
        return self.timestamp + self.length

    @abstractmethod
    def to_string(self) -> str:
        return ""

    def __str__(self):
        return self.to_string()

    def to_dict(self):
        return dataclasses.asdict(self)

    def _common_attributes_to_printable_str_list(self) -> List[str]:
        waveform_type_string = "Type="
        if self.is_iq:
            waveform_type_string += f"IQ Type ({'I' if self.iq_info['isI']  else 'Q'})"
        else:
            waveform_type_string += "Single"
        return [
            f"Waveform Name={self.waveform_name}",
            f"Pulse name={self.pulse_name.removeprefix('OriginPulseName=')}",
            f"Start Time={self.timestamp} ns",
            f"Length={self.length} ns",
            f"Element={self.element}",
            f"Output Ports={self.output_ports}",
            waveform_type_string,
        ]


def format_float(f) -> str:
    return "{:.3f}".format(f)


def pretty_string_freq(f) -> str:
    if f < 1000:
        div, units = 1, "Hz"
    elif 1000 <= f < 1_000_000:
        div, units = 1000, "kHz"
    else:
        div, units = 10e6, "MHz"
    return f"{format_float(f/div).rstrip('0').rstrip('.')}{units}"


@dataclass(frozen=True)
class PlayedAnalogWaveform(PlayedWaveform):
    current_amp_elements: List[float]
    current_dc_offset_by_port: Dict[str, float]
    current_intermediate_frequency: float
    current_frame: List[float]
    current_correction_elements: List[float]
    chirp_info: Optional[Dict]
    current_phase: float

    @classmethod
    def from_job_dict(cls, dict_description: Dict):
        pulse_chirp_info = dict_description["chirpInfo"]
        is_pulse_have_chirp = (
            len(pulse_chirp_info["units"]) > 0 or len(pulse_chirp_info["rate"]) > 0
        )
        formated_attribute_list = dict(
            current_amp_elements=dict_description["currentGMatrixElements"],
            current_dc_offset_by_port=dict_description["currentDCOffsetByPort"],
            current_intermediate_frequency=dict_description[
                "currentIntermediateFrequency"
            ],
            current_frame=dict_description["currentFrame"],
            current_correction_elements=dict_description["currentCorrectionElements"],
            chirp_info=pulse_chirp_info if is_pulse_have_chirp else None,
            current_phase=dict_description.get("currentPhase", 0),
        )
        return super(cls, cls).from_job_dict(dict_description, formated_attribute_list)

    def _to_custom_string(self, show_chirp=True) -> str:
        _attributes = super()._common_attributes_to_printable_str_list()
        _attributes += (
            [
                f"{k}={v if self.is_iq else v[0]}"
                for k, v in [
                    (
                        "Amplitude Values",
                        [format_float(f) for f in self.current_amp_elements],
                    ),
                    (
                        "Frame Values",
                        [format_float(f) for f in self.current_frame],
                    ),
                    (
                        "Correction Values",
                        [format_float(f) for f in self.current_correction_elements],
                    ),
                ]
            ]
            + [
                f"Intermediate Frequency={pretty_string_freq(self.current_intermediate_frequency)}",
                f"Current DC Offset (By output ports)={ {k: format_float(v) for k, v in self.current_dc_offset_by_port.items()} }",
                f"Current Phase={format_float(self.current_phase)},",
            ]
            + (
                []
                if (self.chirp_info is None or not show_chirp)
                else [f"chirp_info={self.chirp_info}"]
            )
        )
        s = (
            "AnalogWaveform("
            + ("\n" + len("AnalogWaveform(") * " ").join(_attributes)
            + ")"
        )
        return s

    def to_string(self) -> str:
        return self._to_custom_string()


@dataclass(frozen=True)
class PlayedDigitalWaveform(PlayedWaveform):
    @classmethod
    def from_job_dict(cls, dict_description: Dict):
        return super(cls, cls).from_job_dict(dict_description, {})

    def to_string(self) -> str:
        s = (
            "DigitalWaveform("
            + ("\n" + len("DigitalWaveform(") * " ").join(
                self._common_attributes_to_printable_str_list()
            )
            + ")"
        )
        return s


@dataclass(frozen=True)
class AdcAcquisition:
    start_time: int
    end_time: int
    process: str
    pulser: Dict[str, dict]
    quantum_element: str
    adc_ports: List[int]
    controller: str

    @classmethod
    def from_job_dict(cls, dict_description: Dict):
        return cls(
            start_time=int(dict_description["startTime"]),
            end_time=int(dict_description["endTime"]),
            process=dict_description["process"],
            pulser=dict_description["pulser"],
            quantum_element=dict_description["quantumElement"],
            adc_ports=[int(p) + 1 for p in dict_description["adc"]],
            controller=dict_description["pulser"]["controllerName"],
        )

    @property
    def ports(self):
        return self.adc_ports

    def to_string(self) -> str:
        return (
            "AdcAcquisition("
            + ("\n" + len("AdcAcquisition(") * " ").join(
                [
                    f"start_time={self.start_time}",
                    f"end_time={self.end_time}",
                    f"process={self.process}",
                    f"element={self.quantum_element}",
                    f"input_ports={self.adc_ports}",
                ]
            )
            + ")"
        )

    def to_dict(self):
        return dataclasses.asdict(self)


class WaveformReport:
    def __init__(self, descriptor_dict: Optional[Dict] = None, job_id=-1):
        self.analog_waveforms: List[PlayedAnalogWaveform] = []
        self.digital_waveforms: List[PlayedDigitalWaveform] = []
        self.adc_acquisitions: List[AdcAcquisition] = []
        self.job_id = job_id
        if descriptor_dict is not None:
            for wf in descriptor_dict["analogWaveforms"]:
                self.analog_waveforms.append(PlayedAnalogWaveform.from_job_dict(wf))
            for wf in descriptor_dict["digitalWaveforms"]:
                self.digital_waveforms.append(PlayedDigitalWaveform.from_job_dict(wf))
            if "adcAcquisitions" in descriptor_dict:
                for acq in descriptor_dict["adcAcquisitions"]:
                    self.adc_acquisitions.append(AdcAcquisition.from_job_dict(acq))
        return

    @classmethod
    def from_dict(cls, d: Dict, job_id=-1) -> "WaveformReport":
        return cls(d, job_id)

    @property
    def waveforms(self) -> List[PlayedWaveform]:
        return self.analog_waveforms + self.digital_waveforms

    @property
    def controllers_in_use(self) -> List[str]:
        return list(
            set([c.controller for c in (self.waveforms + self.adc_acquisitions)])
        )

    @property
    def num_controllers_in_use(self) -> int:
        return len(self.controllers_in_use)

    def _sort_ports_dict(self, ports_in_use):
        for k, v in ports_in_use.items():
            ports_in_use[k] = sorted(v)
        return ports_in_use

    def _get_output_ports_in_use(self, src: List, on_controller):
        ports_in_use = {c: set() for c in self.controllers_in_use}
        for ap in src:
            ports_in_use[ap.controller].update(ap.ports)
        self._sort_ports_dict(ports_in_use)
        if on_controller is None:
            if self.num_controllers_in_use == 1:
                return ports_in_use[self.controllers_in_use[0]]
            else:
                return ports_in_use
        else:
            return ports_in_use[on_controller]

    def analog_output_ports_in_use(
        self, on_controller: Optional[str] = None
    ) -> Union[List[int], Dict[str, List[int]]]:
        return self._get_output_ports_in_use(self.analog_waveforms, on_controller)

    def digital_output_ports_in_use(
        self, on_controller: Optional[str] = None
    ) -> Union[List[int], Dict[str, List[int]]]:
        return self._get_output_ports_in_use(self.digital_waveforms, on_controller)

    def adcs_ports_in_use(
        self, on_controller: Optional[str] = None
    ) -> Union[List[int], Dict[str, List[int]]]:
        return self._get_output_ports_in_use(self.adc_acquisitions, on_controller)

    def to_string(self):
        return "\n".join(
            [wf.to_string() for wf in (self.waveforms + self.adc_acquisitions)]
        )

    def _transform_report_by_func(self, func) -> "WaveformReport":
        new_report = WaveformReport(job_id=self.job_id)
        new_report.analog_waveforms = list(filter(func, self.analog_waveforms))
        new_report.digital_waveforms = list(filter(func, self.digital_waveforms))
        new_report.adc_acquisitions = list(filter(func, self.adc_acquisitions))
        return new_report

    def report_by_controllers(self) -> Dict[str, "WaveformReport"]:
        by_controller_map = {k: None for k in self.controllers_in_use}

        def _filter_func(r, conn):
            return r.controller == conn

        for con_name in by_controller_map.keys():
            con_filter = functools.partial(_filter_func, conn=con_name)
            by_controller_map[con_name] = self._transform_report_by_func(con_filter)

        return by_controller_map

    def to_dict(self) -> Dict:
        return {
            "analog_waveforms": [awf.to_dict() for awf in self.analog_waveforms],
            "digital_waveforms": [dwf.to_dict() for dwf in self.digital_waveforms],
            "adc_acquisitions": [acq.to_dict() for acq in self.adc_acquisitions],
        }

    def get_report_by_output_ports(self, on_controller: Optional[str] = None):

        map_by_output_ports = {
            con_name: {
                "analog_out": {
                    k: []
                    for k in self.analog_output_ports_in_use(on_controller=con_name)
                },
                "digital_out": {
                    k: []
                    for k in self.digital_output_ports_in_use(on_controller=con_name)
                },
                "analog_in": {
                    k: [] for k in self.adcs_ports_in_use(on_controller=con_name)
                },
            }
            for con_name in self.controllers_in_use
        }

        for wf in self.analog_waveforms:
            for p in wf.output_ports:
                map_by_output_ports[wf.controller]["analog_out"][p].append(wf)
        for wf in self.digital_waveforms:
            for p in wf.output_ports:
                map_by_output_ports[wf.controller]["digital_out"][p].append(wf)
        for adc in self.adc_acquisitions:
            for p in adc.adc_ports:
                map_by_output_ports[adc.controller]["analog_in"][p].append(adc)

        if on_controller is None:
            if self.num_controllers_in_use == 1:
                return map_by_output_ports[self.controllers_in_use[0]]
            else:
                return map_by_output_ports
        else:
            return map_by_output_ports[on_controller]

    def create_plot(
        self,
        samples: Optional[Iterable] = None,
        controllers: Optional[List[str]] = None,
        plot: bool = True,
        save_path: Optional[str] = None,
    ):

        if save_path is None:
            dirname, filename = "./", f"waveform_report_{self.job_id}"
        else:
            dirname, filename = os.path.split(save_path)
            if filename == "":
                filename = f"waveform_report_{self.job_id}"

        report_by_controllers = self.report_by_controllers()
        filter_func = (
            (lambda item: item[0] in controllers)
            if controllers is not None
            else (lambda x: True)
        )
        for con_name, report in filter(filter_func, report_by_controllers.items()):
            con_samples = None
            if samples is not None:
                con_samples = samples.__getattribute__(con_name)
            con_builder = _WaveformPlotBuilder(report, con_samples, self.job_id)
            con_builder.build()
            if save_path is not None:
                filename = f"waveform_report_{con_name}_{self.job_id}"
                con_builder.save(dirname, filename)
            if plot:
                con_builder.plot()
        return


class _WaveformPlotBuilder:
    def __init__(self, wf_report: WaveformReport, samples=None, job_id=-1):
        self._report = wf_report
        if wf_report.num_controllers_in_use > 1:
            raise RuntimeError(
                f"Plot Builder does not support plotting more than 1 controllers, yet. {os.linesep}"
                "Please provide a report containing a single controller."
            )
        self._samples = samples
        self._job_id = job_id
        self._figure: Union[go.Figure, None] = None
        self._already_registered_qe = set()
        self._colormap = {}
        self._max_parallel_traces_per_row = {}
        return

    @property
    def _num_rows(self) -> int:
        with_samples = self._samples is not None
        num_rows = (
            len(self._report.analog_output_ports_in_use())
            + len(self._report.digital_output_ports_in_use())
        ) * (1 + with_samples)
        num_rows += len(self._report.adcs_ports_in_use())
        return num_rows

    @property
    def _num_output_rows(self) -> int:
        return self._num_rows - len(self._report.adcs_ports_in_use())

    @property
    def _num_analog_rows(self) -> int:
        return len(self._report.analog_output_ports_in_use()) * (
            1 + (self._samples is not None)
        )

    @property
    def _num_digital_rows(self) -> int:
        return len(self._report.digital_output_ports_in_use()) * (
            1 + (self._samples is not None)
        )

    def _is_row_analog(self, r) -> bool:
        return 1 <= r <= self._num_analog_rows

    def _is_row_digital(self, r) -> bool:
        return self._num_analog_rows < r <= self._num_output_rows

    def _is_row_analog_input(self, r) -> bool:
        return self._num_output_rows < r <= self._num_rows

    @property
    def _xrange(self) -> int:
        return (
            len(self._samples.analog["1"])
            if self._samples is not None
            else max(self._report.waveforms, key=lambda x: x.ends_at).ends_at + 100
        )

    def _pre_setup(self):
        self._setup_qe_colorscale()
        self._calculate_max_parallel_traces_per_row()
        return

    def _get_all_qe_used(self):
        return list(set([wf.element for wf in self._report.waveforms]))

    def _setup_qe_colorscale(self):
        qe_in_use = self._get_all_qe_used()
        n_colors = len(qe_in_use)
        samples = plotly.colors.qualitative.Pastel + plotly.colors.qualitative.Safe
        if n_colors > len(samples):
            samples += plotly.colors.sample_colorscale(
                "turbo",
                [n / (n_colors - len(samples)) for n in range(n_colors - len(samples))],
            )
        self._colormap = dict(zip(qe_in_use, samples))
        return

    def _calculate_max_parallel_traces_per_row(self):
        report_by_output_port = self._report.get_report_by_output_ports()
        self._max_parallel_traces_per_row["analog"] = {}
        self._max_parallel_traces_per_row["digital"] = {}

        def calc_row(waveform_list):
            max_in_row = 0
            functional_ts = sorted(
                [(r.timestamp, 1) for r in waveform_list]
                + [(r.ends_at, -1) for r in waveform_list],
                key=lambda t: t[0],
            )
            for _, f in functional_ts:
                max_in_row = max(max_in_row, max_in_row + f)
            return max_in_row

        for output_port, waveform_list in report_by_output_port["analog_out"].items():
            self._max_parallel_traces_per_row["analog"][output_port] = calc_row(
                waveform_list
            )

        for output_port, waveform_list in report_by_output_port["digital_out"].items():
            self._max_parallel_traces_per_row["digital"][output_port] = calc_row(
                waveform_list
            )

        return

    def _is_intersect(self, r1: Tuple[int, int], r2: Tuple[int, int]) -> bool:
        return (
            (r1[0] <= r2[0] <= r1[1])
            or (r1[0] <= r2[1] <= r1[1])
            or (r2[0] < r1[0] and r2[1] > r1[1])
        )

    def _get_hover_text(self, played_waveform):
        waveform_desc = played_waveform.to_string()
        if isinstance(played_waveform, PlayedAnalogWaveform):
            if played_waveform.chirp_info is not None:
                waveform_desc = played_waveform._to_custom_string(False)
                s = (
                    f"rate={played_waveform.chirp_info['rate']},units={played_waveform.chirp_info['units']},"
                    f" times={played_waveform.chirp_info['times']}\n"
                    + f"start_freq={pretty_string_freq(played_waveform.chirp_info['startFrequency'])}, "
                    + f"end_freq={pretty_string_freq(played_waveform.chirp_info['endFrequency'])}"
                )

                waveform_desc = f"<b>Chirp Pulse</b>\n({s})\n" + waveform_desc
        return "%{x}ns<br>" + waveform_desc.replace("\n", "</br>") + "<extra></extra>"

    def _get_output_port_waveform_plot_data(
        self, port_played_waveforms: List[PlayedWaveform], gui_args
    ):
        graph_data = []
        annotations = []
        levels = []
        x_axis_name = gui_args["x_axis_name"]
        max_in_row = gui_args["max_in_row"]
        diff_between_traces, start_y = (
            (0.2, 1.2) if max_in_row <= 7 else (1.4 / max_in_row, 1.45)
        )
        y_level = [start_y] * 3
        for wf in port_played_waveforms:
            x_axis_points = (wf.timestamp, wf.ends_at)
            num_intersections = len(
                [l for l in levels if self._is_intersect(l, x_axis_points)]
            )
            levels.append(x_axis_points)
            prev_y = start_y if num_intersections == 0 else y_level[0]
            y_level = [prev_y - diff_between_traces] * 3
            graph_data.append(
                go.Scatter(
                    x=[x_axis_points[0], sum(x_axis_points) // 2, x_axis_points[1]],
                    y=y_level,
                    mode="lines+markers+text",
                    text=[
                        "",
                        f"{wf.pulse_name.removeprefix('OriginPulseName=')}"
                        + (f"({wf.get_iq_association})" if wf.is_iq else ""),
                        "",
                    ],
                    hovertemplate=self._get_hover_text(wf),
                    textfont=dict(size=10),
                    xaxis=x_axis_name,
                    name=wf.element,
                    legendgroup=wf.element,
                    showlegend=not (wf.element in self._already_registered_qe),
                    marker=dict(
                        line=dict(width=2, color=self._colormap[wf.element]),
                        symbol=["line-ns", "line-ew", "line-ns"],
                    ),
                    line=dict(color=self._colormap[wf.element], width=5),
                )
            )
            self._already_registered_qe.add(wf.element)

        return graph_data, annotations

    def _add_plot_data_for_analog_output_port(
        self, figure_row_number, output_port, port_waveforms: List[PlayedWaveform]
    ):
        if len(port_waveforms) == 0:
            return
        use_samples = self._samples is not None

        xaxis_name = f"x{figure_row_number}"
        port_wf_plot, annotations = self._get_output_port_waveform_plot_data(
            port_waveforms,
            {
                "x_axis_name": xaxis_name,
                "max_in_row": self._max_parallel_traces_per_row["analog"][output_port],
            },
        )
        row_number = figure_row_number * (1 + use_samples)
        self._figure.add_traces(port_wf_plot, rows=row_number, cols=1)
        [
            self._figure.add_annotation(annot, row=row_number, col=1)
            for annot in annotations
        ]

        if use_samples:
            port_samples = self._samples.analog[str(output_port)]

            self._figure.add_trace(
                go.Scatter(
                    y=port_samples,
                    showlegend=False,
                    xaxis=xaxis_name,
                    hovertemplate="%{x}ns, %{y}v<extra></extra>",
                ),
                row=(figure_row_number * 2 - 1),
                col=1,
            )

        return

    def _add_plot_data_for_digital_output_port(
        self, figure_row_number, output_port, port_waveforms: List[PlayedWaveform]
    ):
        if len(port_waveforms) == 0:
            return
        use_samples = self._samples is not None

        xaxis_name = f"x{figure_row_number}"
        port_wf_plot, annotations = self._get_output_port_waveform_plot_data(
            port_waveforms,
            {
                "x_axis_name": xaxis_name,
                "max_in_row": self._max_parallel_traces_per_row["digital"][output_port],
            },
        )
        row_number = figure_row_number * (1 + use_samples)
        self._figure.add_traces(port_wf_plot, rows=row_number, cols=1)
        [
            self._figure.add_annotation(annot, row=row_number, col=1)
            for annot in annotations
        ]

        if use_samples:
            port_samples = self._samples.digital.get(
                str(output_port), np.zeros(shape=self._xrange)
            )
            if port_samples is None:
                logging.log(
                    logging.WARNING,
                    f"Could not find digital samples for output port {output_port}",
                )
            else:
                port_samples = port_samples.astype(int)
            samples_row_number = figure_row_number * 2 - 1
            self._figure.add_trace(
                go.Scatter(
                    y=port_samples,
                    showlegend=False,
                    xaxis=xaxis_name,
                    hovertemplate="%{x}ns, %{y}<extra></extra>",
                ),
                row=samples_row_number,
                col=1,
            )

        return

    def _add_plot_data_for_adc_port(
        self,
        figure_row_number,
        adc_port_number,
        adc_port_acquisitions: List[AdcAcquisition],
    ):
        graph_data = []
        levels = []
        y_level = [1.2] * 3
        for adc in adc_port_acquisitions:
            x_axis_points = (adc.start_time, adc.end_time)
            num_intersections = len(
                [l for l in levels if self._is_intersect(l, x_axis_points)]
            )
            levels.append(x_axis_points)
            prev_y = 1.2 if num_intersections == 0 else y_level[0]
            y_level = [prev_y - 0.2] * 3
            graph_data.append(
                go.Scatter(
                    x=[x_axis_points[0], sum(x_axis_points) // 2, x_axis_points[1]],
                    y=y_level,
                    mode="lines+markers+text",
                    text=[
                        "",
                        f"{adc.process}",
                        "",
                    ],
                    textfont=dict(size=10),
                    hovertemplate="%{x}ns<br>"
                    + adc.to_string().replace("\n", "</br>")
                    + "<extra></extra>",
                    name=adc.quantum_element,
                    legendgroup=adc.quantum_element,
                    showlegend=not (adc.quantum_element in self._already_registered_qe),
                    marker=dict(
                        line=dict(width=2, color=self._colormap[adc.quantum_element]),
                        symbol=["line-ns", "line-ew", "line-ns"],
                    ),
                    line=dict(color=self._colormap[adc.quantum_element], width=5),
                )
            )
            self._already_registered_qe.add(adc.quantum_element)

        self._figure.add_traces(graph_data, rows=figure_row_number, cols=1)

        return

    def _add_data(self):
        for (figure_row_number, (output_port, port_waveforms_list)) in enumerate(
            self._report.get_report_by_output_ports()["analog_out"].items()
        ):
            self._add_plot_data_for_analog_output_port(
                figure_row_number + 1, output_port, port_waveforms_list
            )

        for (figure_row_number, (output_port, port_waveforms_list)) in enumerate(
            self._report.get_report_by_output_ports()["digital_out"].items()
        ):
            self._add_plot_data_for_digital_output_port(
                figure_row_number + len(self._report.analog_output_ports_in_use()) + 1,
                output_port,
                port_waveforms_list,
            )

        for (figure_row_number, (input_port, adc_acquisition_list)) in enumerate(
            self._report.get_report_by_output_ports()["analog_in"].items()
        ):
            self._add_plot_data_for_adc_port(
                figure_row_number + self._num_output_rows + 1,
                input_port,
                adc_acquisition_list,
            )
        return

    def _update_extra_features(self):
        all_xaxis_names = sorted(
            [a for a in self._figure.layout.__dir__() if a.startswith("xaxis")],
            key=lambda s: int(s.removeprefix("xaxis"))
            if s.removeprefix("xaxis").isnumeric()
            else 0,
        )
        all_xaxis_names_short = {
            k: "x" + k.removeprefix("xaxis")
            if k.removeprefix("xaxis").isnumeric()
            else ""
            for k in all_xaxis_names
        }
        bottomost_x_axis = all_xaxis_names[-1]
        self._figure.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    active=0,
                    buttons=list(
                        [
                            dict(
                                args=[
                                    {
                                        k
                                        + ".matches": all_xaxis_names_short[
                                            bottomost_x_axis
                                        ]
                                        for k in all_xaxis_names
                                    }
                                ],
                                label="Shared",
                                method="relayout",
                            ),
                            dict(
                                args=[
                                    {
                                        k + ".matches": v
                                        for k, v in all_xaxis_names_short.items()
                                    }
                                ],
                                label="Distinct",
                                method="relayout",
                            ),
                        ]
                    ),
                    showactive=True,
                    x=1,
                    xanchor="right",
                    y=1,
                    yanchor="bottom",
                    font=dict(size=10),
                ),
            ]
        )
        self._figure.add_annotation(
            dict(
                text="X-Axis scrolling method:",
                showarrow=False,
                x=1,
                y=1,
                yref="paper",
                yshift=40,
                yanchor="bottom",
                xref="paper",
                align="left",
            )
        )
        self._figure.update_layout(
            modebar_remove=[
                "autoscale",
                "autoscale2d",
                "lasso",
            ]
        )

        source_path = os.path.join(
            os.path.dirname(__file__), "sources", "logo_qm_square.png"
        )

        im = base64.b64encode(open(source_path, "rb").read())
        self._figure.add_layout_image(
            source="data:image/png;base64,{}".format(im.decode()),
            xref="paper",
            yref="paper",
            x=0,
            y=1,
            sizex=0.1,
            sizey=0.1,
            xanchor="center",
            yanchor="bottom",
        )
        return

    def _setup_figure(self):
        self._figure = go.Figure()
        with_samples = self._samples is not None
        num_rows = max(self._num_rows, 4)
        titles = [
            f"Analog-Out-{a}" for a in self._report.analog_output_ports_in_use()
        ] + [f"Digital-Out-{d}" for d in self._report.digital_output_ports_in_use()]
        if with_samples:
            zipped = list(zip(titles, [[]] * self._num_output_rows))
            titles = [item for z in zipped for item in z]
        titles += [f"Analog-In-{a}" for a in self._report.adcs_ports_in_use()]

        if with_samples:
            specs = (
                [[{"t": 1.2 / (num_rows * 5)}]] + [[{"b": 1.2 / (num_rows * 5)}]]
            ) * (self._num_output_rows // 2) + [[{"t": 1 / (num_rows * 4)}]] * len(
                self._report.adcs_ports_in_use()
            )
        else:
            specs = [[{"t": 1 / (num_rows * 4)}]] * num_rows
        self._figure.set_subplots(
            rows=num_rows,
            cols=1,
            subplot_titles=titles,
            vertical_spacing=0.1 / num_rows,
            specs=specs,
        )

        self._figure.update_layout(
            hovermode="closest",
            hoverdistance=5,
            height=160 * num_rows,
            title=dict(
                text=(
                    f"Waveform Report (connection: {self._report.controllers_in_use[0]})"
                    + (
                        " for job: {}".format(self._job_id)
                        if self._job_id != -1
                        else ""
                    )
                ),
                x=0.5,
                xanchor="center",
                yanchor="auto",
                xref="paper",
            ),
            legend=dict(title="Elements", y=0.98, yanchor="top"),
        )
        self._figure.add_annotation(
            dict(
                text=f"Created at {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                showarrow=False,
                x=0.5,
                y=1,
                yref="paper",
                yshift=20,
                yanchor="bottom",
                xref="paper",
                xanchor="center",
            )
        )

        for r in range(1, num_rows + 1):
            self._figure.update_xaxes(range=[0, self._xrange], row=r, col=1)

        if with_samples:
            for r in range(1, self._num_output_rows, 2):
                if self._is_row_digital(r):
                    sample_y_range = [-0.1, 1.1]
                else:
                    sample_y_range = [-0.6, 0.6]
                self._figure.update_yaxes(
                    range=sample_y_range,
                    row=r,
                    col=1,
                )
                self._figure.update_xaxes(showticklabels=False, row=r, col=1)
                title_text = "Voltage(v)"
                self._figure.update_yaxes(
                    title=dict(text=title_text, standoff=5, font=dict(size=9)),
                    row=r,
                    col=1,
                )

        for r in list(
            range(1 + with_samples, self._num_output_rows + 1, 1 + with_samples)
        ) + [p + self._num_output_rows for p in self._report.adcs_ports_in_use()]:
            self._figure.update_yaxes(
                range=[-0.5, 1.5],
                showticklabels=False,
                tickvals=[-0.5],
                ticklen=50,
                tickcolor="#000000",
                showgrid=False,
                zeroline=False,
                row=r,
                col=1,
            )
            self._figure.update_xaxes(
                title=dict(text="Time(ns)", standoff=5, font=dict(size=9)), row=r, col=1
            )
            title_text = ""

        return

    def build(self):
        self._pre_setup()
        self._setup_figure()
        self._add_data()
        self._update_extra_features()
        return

    def plot(self):
        if self._figure is None:
            raise RuntimeError(
                "No graph has been built. Use 'build' on the instance to first build the figure."
            )
        self._figure.show()
        return

    def save(self, basedir="", filename=""):
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        if filename == "":
            filename = f"waveform_report_{self._job_id}"
        if not os.path.splitext(filename)[1] == "html":
            filename += ".html"

        path = os.path.join(basedir, filename)
        with open(path, "w") as f:
            self._figure.write_html(f)
        return
