from app.config.settings import Settings, get_settings


def test_settings_load():
    """
    Test that Settings loads cleanly with expected defaults according to CLAUDE.md.
    """
    settings = get_settings()
    assert settings.app_name == "FailureFoundry"
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert "failurefoundry.db" in settings.database_url
    # CLAUDE.md §21: verified host is prism.blockconvey.com, not api.blockconvey.com
    assert settings.prism_base_url == "https://prism.blockconvey.com"
