import httpx
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from app.config import settings

HOP_BY_HOP = {
    "host",
    "content-length",
    "connection",
    "transfer-encoding",
    "keep-alive",
    "upgrade",
}


def _merge_headers(h: httpx.Headers) -> dict:
    out = {k: v for k, v in h.items() if k.lower() not in HOP_BY_HOP}
    sid = h.get("mcp-session-id") or h.get("Mcp-Session-Id") or h.get("MCP-SESSION-ID")
    if sid:
        # set both; HTTP/2 will render lowercase on the wire anyway
        out["mcp-session-id"] = sid
        out["Mcp-Session-Id"] = sid
    return out


async def proxy_streamable_http(req: Request, tail: str = "") -> Response:
    upstream = (
        f"{settings.UPSTREAM_MCP_URL}/{tail}" if tail else settings.UPSTREAM_MCP_URL
    )
    fwd_headers = {k: v for k, v in req.headers.items() if k.lower() not in HOP_BY_HOP}
    fwd_headers["X-API-KEY"] = settings.UPSTREAM_MCP_KEY

    method = req.method.upper()
    async with httpx.AsyncClient(timeout=None) as client:
        if method in ("GET", "DELETE"):
            upstream_res = await client.stream(
                method, upstream, headers=fwd_headers, params=dict(req.query_params)
            )
            headers = _merge_headers(upstream_res.headers)

            async def aiter():
                async for chunk in upstream_res.aiter_raw():
                    yield chunk

            return StreamingResponse(
                aiter(),
                status_code=upstream_res.status_code,
                media_type=upstream_res.headers.get("content-type") or None,
                headers=headers,
            )
        else:
            body = await req.body()
            upstream_res = await client.request(
                method, upstream, headers=fwd_headers, content=body
            )
            headers = _merge_headers(upstream_res.headers)
            return Response(
                content=upstream_res.content,
                status_code=upstream_res.status_code,
                media_type=upstream_res.headers.get("content-type"),
                headers=headers,
            )
