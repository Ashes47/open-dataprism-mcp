from fastapi import FastAPI, Request
from app.proxy import proxy_streamable_http

app = FastAPI(title="dataprism-mcp-min", docs_url=None, redoc_url=None, openapi_url=None)

# MCP endpoints only
@app.api_route("/mcp", methods=["GET", "POST"])
async def mcp_root(req: Request):
    return await proxy_streamable_http(req, "")

@app.api_route("/mcp/{tail:path}", methods=["GET", "POST"])
async def mcp_any(req: Request, tail: str):
    return await proxy_streamable_http(req, tail)
