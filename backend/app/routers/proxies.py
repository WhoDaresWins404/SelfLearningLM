from fastapi import APIRouter, HTTPException

from backend.app.schemas.proxy import ProxyCreate, ProxyResponse
from backend.app.services import proxy_service

router = APIRouter(prefix="/api/proxies", tags=["proxies"])


@router.get("")
def list_proxies(enabled_only: bool = False):
    proxies = proxy_service.list_proxies(enabled_only=enabled_only)
    return [
        ProxyResponse(id=p.id, address=p.address, enabled=bool(p.enabled), failures=p.failures)
        for p in proxies
    ]


@router.post("", status_code=201)
def add_proxy(body: ProxyCreate):
    p = proxy_service.add_proxy(body.address)
    return ProxyResponse(id=p.id, address=p.address, enabled=bool(p.enabled), failures=p.failures)


@router.put("/{proxy_id}/toggle")
def toggle_proxy(proxy_id: int, enabled: bool = True):
    p = proxy_service.toggle_proxy(proxy_id, enabled)
    if not p:
        raise HTTPException(404, "Proxy not found")
    return ProxyResponse(id=p.id, address=p.address, enabled=bool(p.enabled), failures=p.failures)


@router.delete("/{proxy_id}")
def delete_proxy(proxy_id: int):
    if not proxy_service.delete_proxy(proxy_id):
        raise HTTPException(404, "Proxy not found")
    return {"ok": True}


@router.post("/sync")
def sync_proxies():
    proxy_service.sync_proxies_from_file()
    return {"ok": True}
