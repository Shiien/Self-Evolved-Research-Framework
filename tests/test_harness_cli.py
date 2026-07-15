from harness import cli


def test_smoke_test_environment_disables_external_pytest_plugins(monkeypatch):
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)

    env = cli._smoke_test_env()

    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert env["SER_TDNL_DISABLE_ENGINE"] == "1"
