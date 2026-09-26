"""Maps Yahoo's short exchange codes to our own exchange details.

Codes and behaviour verified empirically against Yahoo Finance in Phase 4A
(scripts/explore_exchanges.py) rather than assumed from documentation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExchangeInfo:
    exchange_code: str  # our internal code (loosely ISO 10383 MIC-style)
    exchange_name: str
    country: str  # ISO 3166 alpha-2
    currency: str  # ISO 4217
    native_suffix: str  # what Yahoo appends, e.g. ".T"; "" for US


# Keyed by Yahoo's short "exchange" field, as seen in search results
# and in Ticker(...).history_metadata()["exchangeName"].
_REGISTRY: dict[str, ExchangeInfo] = {
    "NMS": ExchangeInfo("XNAS", "Nasdaq", "US", "USD", ""),
    "NYQ": ExchangeInfo("XNYS", "New York Stock Exchange", "US", "USD", ""),
    "PCX": ExchangeInfo("ARCX", "NYSE Arca", "US", "USD", ""),
    "SES": ExchangeInfo("XSES", "Singapore Exchange", "SG", "SGD", ".SI"),
    "HKG": ExchangeInfo("XHKG", "Hong Kong Stock Exchange", "HK", "HKD", ".HK"),
    "SHH": ExchangeInfo("XSHG", "Shanghai Stock Exchange", "CN", "CNY", ".SS"),
    "SHZ": ExchangeInfo("XSHE", "Shenzhen Stock Exchange", "CN", "CNY", ".SZ"),
    "JPX": ExchangeInfo("XJPX", "Tokyo Stock Exchange", "JP", "JPY", ".T"),
    "KSC": ExchangeInfo("XKRX", "Korea Exchange", "KR", "KRW", ".KS"),
    "TAI": ExchangeInfo("XTAI", "Taiwan Stock Exchange", "TW", "TWD", ".TW"),
}


def get_exchange_info(yahoo_code: str) -> ExchangeInfo | None:
    return _REGISTRY.get(yahoo_code)


def is_supported_exchange(yahoo_code: str) -> bool:
    return yahoo_code in _REGISTRY


def to_native_symbol(provider_symbol: str, yahoo_code: str) -> str:
    """Strip Yahoo's market suffix, e.g. '7203.T' -> '7203'."""
    info = get_exchange_info(yahoo_code)
    if info and info.native_suffix and provider_symbol.endswith(info.native_suffix):
        return provider_symbol[: -len(info.native_suffix)]
    return provider_symbol
