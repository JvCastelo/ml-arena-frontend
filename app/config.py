from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Config do frontend — não confundir `secret_key` com o `secret_key` do
    backend: aqui é só pra assinar o cookie de sessão (Starlette
    `SessionMiddleware`), lá é pra assinar o JWT. São segredos diferentes."""

    api_base_url: str = "http://127.0.0.1:8000"
    secret_key: str = "dev-only-change-me"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
