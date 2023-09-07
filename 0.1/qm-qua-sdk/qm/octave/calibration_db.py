import os
import logging
from pathlib import Path
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Union, Optional

from tinydb import Query, TinyDB

from qm.type_hinting.config_types import DictQuaConfig

logger = logging.getLogger(__name__)


@dataclass
class CalibrationResult:
    correction: List[float]
    i_offset: float
    q_offset: float
    lo_frequency: float
    if_frequency: float
    temperature: float
    mixer_id: str
    optimizer_parameters: Dict[str, Any]


class CalibrationDB:
    def __init__(self, path: Union[str, Path]) -> None:
        super().__init__()
        file_name = "calibration_db.json"
        self._file_path = os.path.join(path, file_name)
        self._db = TinyDB(self._file_path)

    @property
    def file_path(self):
        return self._file_path

    def update_calibration_data(self, data: Union[CalibrationResult, List[CalibrationResult]]):
        if isinstance(data, CalibrationResult):
            data = [data]

        query = Query()
        for result in data:
            self._db.upsert(
                asdict(result),
                (query.mixer_id == result.mixer_id)
                & (query.lo_frequency == result.lo_frequency)
                & (query.if_frequency == result.if_frequency),
            )

    def get(self, mixer, lo_freq, if_freq) -> Optional[CalibrationResult]:
        query = Query()
        doc = self._db.get(
            (query.mixer_id == mixer) & (query.lo_frequency == lo_freq) & (query.if_frequency == if_freq),
        )
        if doc is not None:
            return self._doc_to_result(doc)
        else:
            raise AttributeError(f"calibration for {mixer}, lo {lo_freq}, if {if_freq} was not found")

    def get_or_none(self, mixer, lo_freq, if_freq) -> Optional[CalibrationResult]:
        query = Query()
        doc = self._db.get(
            (query.mixer_id == mixer) & (query.lo_frequency == lo_freq) & (query.if_frequency == if_freq)
        )
        if doc is not None:
            return self._doc_to_result(doc)
        else:
            return None

    def get_for_lo_frequency(self, mixer, lo_freq) -> List[CalibrationResult]:
        query = Query()
        table = self._db.search((query.mixer_id == mixer) & (query.lo_frequency == lo_freq))
        return [self._doc_to_result(doc) for doc in table]

    def get_all(self, mixer) -> List[CalibrationResult]:
        l = self.get_all_or_default(mixer)
        if len(l) > 0:
            return l
        else:
            raise AttributeError(f"calibration for {mixer} was not found")

    def get_all_or_default(self, mixer) -> Optional[List[CalibrationResult]]:
        query = Query()
        table = self._db.search(query.mixer_id == mixer)
        l = [self._doc_to_result(doc) for doc in table]
        return l

    def __getitem__(self, item):
        return self.get(*item)

    @staticmethod
    def _doc_to_result(doc):
        return CalibrationResult(
            correction=doc["correction"],
            i_offset=doc["i_offset"],
            q_offset=doc["q_offset"],
            if_frequency=doc["if_frequency"],
            lo_frequency=doc["lo_frequency"],
            temperature=doc["temperature"],
            optimizer_parameters=doc["optimizer_parameters"],
            mixer_id=doc["mixer_id"],
        )

    def __del__(self):
        self._db.close()


def octave_output_mixer_name(octave: str, port: int) -> str:
    return f"octave_{octave}_{port}"


def load_from_calibration_db(config: DictQuaConfig, calibration_db: CalibrationDB) -> None:
    if calibration_db is None:
        return
    for mixer in config["mixers"].keys():
        cal_list = calibration_db.get_all_or_default(mixer)
        cal_dict = {(v.lo_frequency, v.if_frequency): v.correction for v in cal_list}
        if len(cal_list) > 0:
            old_values = config["mixers"][mixer]
            new_values = [
                {
                    "intermediate_frequency": int(v.if_frequency),
                    "lo_frequency": int(v.lo_frequency),
                    "correction": v.correction,
                }
                for v in cal_list
            ]

            for v in old_values:
                if (v["lo_frequency"], v["intermediate_frequency"]) in cal_dict:
                    pass
                else:
                    new_values.append(v)
                    logger.debug(
                        f"Could not find calibration value for lo frequency"
                        f" {v['lo_frequency']} and intermediate_frequency"
                        f" {v['intermediate_frequency']}"
                    )

            config["mixers"][mixer] = new_values

            # changing offsets here because we know the mixer is octave
            for element in config["elements"].values():
                if (
                    "mixInputs" in element
                    and element["mixInputs"]["mixer"] == mixer
                    and "intermediate_frequency" in element
                ):
                    if_freq = element["intermediate_frequency"]
                    lo_freq = element["mixInputs"]["lo_frequency"]
                    i_port = element["mixInputs"]["I"]
                    q_port = element["mixInputs"]["Q"]
                    result = calibration_db.get_or_none(mixer, lo_freq, if_freq)
                    if result is not None:
                        config["controllers"][i_port[0]]["analog_outputs"][i_port[1]]["offset"] = result.i_offset
                        config["controllers"][q_port[0]]["analog_outputs"][q_port[1]]["offset"] = result.q_offset
