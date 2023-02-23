import os
import json
import uuid
from typing import Optional, Union
from dataclasses import dataclass, field, asdict

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".qm", "config.json")


@dataclass
class UserConfig:
    SESSION_ID = uuid.uuid4()
    quantumMachinesManager_port: Optional[int] = field(default=None)
    quantumMachinesManager_host: Optional[str] = field(default=None)
    quantumMachinesManager_strict_healthcheck: bool = field(default=True)
    quantumMachinesManager_user_token: str = field(default="")
    quantumMachinesManager_managerPort: Optional[int] = field(default=None)
    # This field is not is use anymore
    logging_level: Union[int, str] = field(default="INFO")
    upload_logs: bool = field(default=False)
    datadog_token: str = field(default="")
    organization: str = field(default="Unknown")

    @property
    def manager_port(self):
        return self.quantumMachinesManager_port

    @property
    def manager_host(self):
        return self.quantumMachinesManager_host

    @property
    def strict_healthcheck(self):
        return self.quantumMachinesManager_strict_healthcheck

    @property
    def user_token(self):
        return self.quantumMachinesManager_user_token

    @classmethod
    def create_from_file(cls):
        raw_dict = cls._read_json(CONFIG_PATH)
        return cls(**raw_dict)

    def write_to_file(self):
        config_dict = asdict(self)
        self._write_json(config_dict, CONFIG_PATH)

    @staticmethod
    def _read_json(file_path) -> dict:
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                return json.load(file)
        else:
            return {}

    @staticmethod
    def _write_json(config: dict, file_path: str) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            return json.dump(config, file, indent=4)

    @property
    def enable_user_stdout(self):
        return os.environ.get("QM_DISABLE_STREAMOUTPUT", None) is None

    @property
    def default_logging_format(self):
        return "%(asctime)s - qm - %(levelname)-8s - %(message)s"

    @property
    def datadog_handler_config(self):
        assert self.user_token, "No user token is defined"
        return {
            "class": "qm.datadog_api.DatadogHandler",
            "user_id": self.user_token,
            "organization": self.organization,
            "user_token": self.datadog_token,
            "session_id": self.SESSION_ID,
        }

    @property
    def logging_config_dict(self):
        default_formatter = "default"
        formatters = {default_formatter: {"format": self.default_logging_format}}
        handlers = {}
        if self.enable_user_stdout:
            handlers["stdout"] = {
                "class": "logging.StreamHandler",
                "formatter": default_formatter,
                "stream": "ext://sys.stdout",
            }
        if self.upload_logs and self.datadog_token:
            handlers["datadog"] = self.datadog_handler_config
        return {
            "version": 1,
            "formatters": formatters,
            "handlers": handlers,
            "loggers": {
                "qm": {"level": self.logging_level, "handlers": list(handlers)}
            },
        }


def load_user_config():
    return UserConfig.create_from_file()


def _generate_random_id():
    return str(uuid.uuid4()).split("-")[-1]


def update_old_user_config(
    old_config,
    host=None,
    port=None,
    send_anonymous_logs=None,
    datadog_token="",
    organization="Unknown",
):
    user_token = old_config.user_token or _generate_random_id()
    upload_logs = (
        old_config.upload_logs if send_anonymous_logs is None else send_anonymous_logs
    )
    return UserConfig(
        upload_logs=upload_logs,
        quantumMachinesManager_user_token=user_token,
        datadog_token=datadog_token,
        organization=organization,
        quantumMachinesManager_host=host,
        quantumMachinesManager_port=port,
    )


def create_new_user_config(
    host=None,
    port=None,
    send_anonymous_logs=None,
    datadog_token="",
    organization="Unknown",
):
    """Creates a user config file (running it requires writing permission). Setting
    a host and a port removes the need to specify them each time opening a QuantumMachinesManager.
    All parameters are optional.

    Args:
        host: ip of the host (string)
        port: port number (int)
        send_anonymous_logs: (bool) Setting this parameter to `True`
            means you agree to send anonymously the logs that the qm
            module produces.
        datadog_token: string of token to send logs.
        organization: Name of your organization.
    """
    old_config = UserConfig.create_from_file()
    config = update_old_user_config(
        old_config,
        host=host,
        port=port,
        send_anonymous_logs=send_anonymous_logs,
        datadog_token=datadog_token,
        organization=organization,
    )
    config.write_to_file()
