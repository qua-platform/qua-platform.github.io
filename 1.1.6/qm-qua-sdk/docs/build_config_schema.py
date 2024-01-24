import json
from collections import OrderedDict
import pathlib

from qm.program._qua_config_schema import QuaConfigSchema, ArbitraryWaveFormSchema, \
    ConstantWaveFormSchema
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin


def order_props(d, path, order):
    steps = ("definitions" + path).split("/")
    last_step = steps.pop()
    obj = d
    for step in steps:
        obj = obj[step]
    parent_obj = obj
    obj = obj[last_step]

    ordered_keys = list(order) + [k for k in obj.keys() if k not in order]
    parent_obj[last_step] = OrderedDict([(k, obj[k]) for k in ordered_keys])
    return d


def build(version):
    spec_path = str(pathlib.Path(__file__).parent.joinpath("spec.json").absolute())
    lst = [
        (QuaConfigSchema, version, spec_path)
    ]
    for schema, version, specfile in lst:
        spec = APISpec(
            title="Qm Config",
            version=version,
            openapi_version="2.0",
            plugins=[MarshmallowPlugin()],
        )
        spec.components.schema("QmConfig", schema=schema)
        spec.components.schema("ArbitraryWaveform", schema=ArbitraryWaveFormSchema)
        spec.components.schema("ConstantWaveform", schema=ConstantWaveFormSchema)

        base = {
            "/": {
                "get": {
                    "description": "Get config",
                    "responses": {
                        "200": {
                            "descriptions": "The config structure",
                            "schema": {
                                "$ref": "#/definitions/QmConfig"
                            }
                        }
                    }
                }
            }
        }

        spec_dict = spec.to_dict()
        spec_dict["paths"] = base
        spec_dict["definitions"]["QmConfig"]["properties"]["waveforms"][
            "additionalProperties"]["type"] = "object"
        spec_dict["definitions"]["QmConfig"]["properties"]["waveforms"][
            "additionalProperties"]["oneOf"] = [
            {"$ref": "#/definitions/ArbitraryWaveform"},
            {"$ref": "#/definitions/ConstantWaveform"}
        ]

        spec_dict = order_props(spec_dict, "/QmConfig/properties", [
            "version",
            "controllers",
            "elements",
            "pulses",
            "waveforms",
            "digital_waveforms",
            "integration_weights",
            "oscillators",
            "mixers",
        ])

        spec_dict = order_props(spec_dict, "/MixInput/properties", ["I", "Q"])

        with open(specfile, "w") as f:
            json.dump(spec_dict, f, indent=2)

        print("schema created")


def components(schema):
    spec = APISpec(
        title="Qm Config",
        version="x",
        openapi_version="3.0.2",
        plugins=[MarshmallowPlugin()],
    )
    spec.components.schema("QmConfig", schema=schema)
    return spec.to_dict()["components"]


if __name__ == "__main__":
    import qm.version
    build(qm.version.__version__)
