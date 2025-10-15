import httpx
from fastapi import Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from app.config import settings

HOP_BY_HOP = {"host", "content-length", "connection", "transfer-encoding"}

async def proxy_streamable_http(req: Request, tail: str = "") -> Response:
    """
    Minimal Streamable-HTTP proxy (no auth).
    - Preserves POST/GET
    - Passes through SSE (text/event-stream)
    - Injects X-API-KEY to upstream
    """
    upstream = f"{settings.UPSTREAM_MCP_URL}/{tail}" if tail else settings.UPSTREAM_MCP_URL

    fwd_headers = {k: v for k, v in req.headers.items() if k.lower() not in HOP_BY_HOP}
    fwd_headers["X-API-KEY"] = settings.UPSTREAM_MCP_KEY

    method = req.method.upper()
    async with httpx.AsyncClient(timeout=None) as client:
        if method in ("GET", "DELETE"):
            upstream_res = await client.stream(
                method, upstream, headers=fwd_headers, params=dict(req.query_params)
            )
            status_code = upstream_res.status_code
            headers = dict(upstream_res.headers)

            async def aiter():
                async for chunk in upstream_res.aiter_raw():
                    yield chunk

            media_type = headers.get("content-type", "")
            return StreamingResponse(
                aiter(),
                status_code=status_code,
                media_type=media_type or None,
                headers={k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP},
            )
        else:
            body = await req.body()
            upstream_res = await client.request(method, upstream, headers=fwd_headers, content=body)
            content_type = upstream_res.headers.get("content-type", "")
            if "application/json" in content_type:
                return JSONResponse(upstream_res.json(), status_code=upstream_res.status_code)
            return Response(
                content=upstream_res.content,
                status_code=upstream_res.status_code,
                media_type=content_type or None,
            )
