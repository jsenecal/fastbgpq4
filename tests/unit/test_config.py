from app.config import Settings


def test_settings_default_values():
    settings = Settings()
    assert settings.bgpq4_binary == "/usr/bin/bgpq4"
    assert settings.sync_timeout_ms == 1000
    assert settings.max_retries == 3
    assert settings.default_cache_ttl == 300


def test_settings_irr_sources_as_list():
    settings = Settings(irr_sources="RIPE,RADB,ARIN")
    assert settings.irr_sources == ["RIPE", "RADB", "ARIN"]


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("SYNC_TIMEOUT_MS", "2000")
    monkeypatch.setenv("MAX_RETRIES", "5")
    settings = Settings()
    assert settings.sync_timeout_ms == 2000
    assert settings.max_retries == 5
