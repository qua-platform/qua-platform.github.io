from qm.user_config import UserConfig, update_old_user_config


def test_empty_dictionary_does_not_fail_initialization():
    UserConfig()
    assert True


def test_default_of_uploading_logs_is_negative():
    config = UserConfig()
    assert config.upload_logs is False


def test_keeping_old_user_token_when_creating_a_new_config():
    old_config = UserConfig(quantumMachinesManager_user_token="old_token")
    new_config = update_old_user_config(old_config)
    assert new_config.user_token == "old_token"


def test_creating_token_when_no_old_token_exists():
    old_config = UserConfig()
    assert old_config.user_token == ""
    new_config = update_old_user_config(old_config)
    assert new_config.user_token


def test_uploading_logs_consent_status_is_kept_when_creating_a_new_config():
    old_config = UserConfig()
    new_config = update_old_user_config(old_config)
    assert new_config.upload_logs is False

    old_config = UserConfig(upload_logs=True)
    new_config = update_old_user_config(old_config)
    assert new_config.upload_logs is True


def test_upload_logs_consent_is_overriden_when_provided():
    old_config = UserConfig()
    new_config = update_old_user_config(old_config, send_anonymous_logs=True)
    assert new_config.upload_logs is True
    newer_config = update_old_user_config(old_config, send_anonymous_logs=False)
    assert newer_config.upload_logs is False
