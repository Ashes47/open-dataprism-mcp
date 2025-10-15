import os


class Settings:
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://mcp.dataprism.dev")

    # Upstream MCP (real server)
    UPSTREAM_MCP_URL = os.getenv(
        "UPSTREAM_MCP_URL", "https://platform.dataprism.dev/mcp"
    )
    UPSTREAM_MCP_KEY = os.getenv("UPSTREAM_MCP_KEY", "REPLACE_ME_STATIC_API_KEY")


settings = Settings()
