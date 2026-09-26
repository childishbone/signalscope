"""Security search endpoint (backed by the market-data provider)."""

from fastapi import APIRouter

from signalscope.api.schemas import SecurityMatchOut
from signalscope.market_data.yahoo import YahooProvider

router = APIRouter(prefix="/api/securities", tags=["securities"])

# One shared provider instance; YahooProvider holds no per-request state.
_provider = YahooProvider()


@router.get("/search", response_model=list[SecurityMatchOut])
def search_securities(q: str, limit: int = 8) -> list[SecurityMatchOut]:
    if not q.strip():
        return []
    matches = _provider.search_securities(q.strip(), limit=limit)
    return [SecurityMatchOut(**match.__dict__) for match in matches]
