import os


class Settings:
    """All configuration comes from environment variables. Nothing secret has a default."""

    # OpenCode gateway (OpenAI-compatible). Key is server-side only.
    OPENCODE_API_KEY: str = os.getenv("OPENCODE_API_KEY", "")
    OPENCODE_BASE_URL: str = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/inference/go/openai/v1")

    # Model routing:
    #  - QUERY_MODEL: fast/cheap model for query building + relaxation planning.
    #  - EVAL_MODEL: the model that judges each job posting (structured JSON accuracy
    #    matters most here). Defaults to flash so it works out of the box; point it at
    #    the strongest model your OpenCode plan routes to for better precision.
    QUERY_MODEL: str = os.getenv("QUERY_MODEL", "deepseek-v4.1-flash")
    EVAL_MODEL: str = os.getenv("EVAL_MODEL", "deepseek-v4.1-flash")

    # Upstash Redis (rediss:// URL from the Upstash console). If unset, an in-memory
    # store is used so local dev works without Redis.
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # Explicit CORS whitelist, comma-separated. No wildcard, ever.
    ALLOWED_ORIGINS: list = [
        o.strip()
        for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]

    # Rate limiting — lifetime limit per IP, no reset
    RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", "2"))

    # Result cache TTL (24h — nothing persists beyond this)
    RESULT_TTL: int = int(os.getenv("RESULT_TTL", "86400"))

    # Pipeline knobs
    MAX_LINKS: int = int(os.getenv("MAX_LINKS", "25"))
    MAX_MATCHES: int = int(os.getenv("MAX_MATCHES", "8"))
    PER_JOB_DELAY: float = float(os.getenv("PER_JOB_DELAY", "3.0"))

    # Contact info surfaced when the rate limit is hit
    CONTACT_LINKEDIN: str = os.getenv(
        "CONTACT_LINKEDIN", "https://www.linkedin.com/in/harshmankar"
    )
    CONTACT_EMAIL: str = os.getenv("CONTACT_EMAIL", "harshrajendramankar@gmail.com")


settings = Settings()
