from app.core.config import Settings


def test_cors_origins_accepts_comma_separated_env(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost")

    settings = Settings()

    assert settings.CORS_ORIGINS == ["http://localhost:3000", "http://localhost"]


def test_cors_origins_accepts_json_array_env(monkeypatch) -> None:
    monkeypatch.setenv(
        "CORS_ORIGINS",
        '["https://example.com","https://www.example.com"]',
    )

    settings = Settings()

    assert settings.CORS_ORIGINS == [
        "https://example.com",
        "https://www.example.com",
    ]
