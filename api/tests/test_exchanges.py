from signalscope.market_data.exchanges import (
    get_exchange_info,
    is_supported_exchange,
    to_native_symbol,
)


def test_all_seven_target_markets_are_registered() -> None:
    codes = {"NMS", "NYQ", "PCX", "SES", "HKG", "SHH", "SHZ", "JPX", "KSC", "TAI"}
    for code in codes:
        assert is_supported_exchange(code), code


def test_disallowed_exchanges_are_rejected() -> None:
    for code in ["PNK", "IOB", "FRA", "NEO", "TOR", "CME", ""]:
        assert not is_supported_exchange(code), code


def test_japan_lookup_has_correct_currency_and_country() -> None:
    info = get_exchange_info("JPX")
    assert info is not None
    assert info.country == "JP"
    assert info.currency == "JPY"


def test_native_symbol_strips_suffix_for_suffixed_markets() -> None:
    assert to_native_symbol("7203.T", "JPX") == "7203"
    assert to_native_symbol("0700.HK", "HKG") == "0700"


def test_native_symbol_unchanged_for_us_markets() -> None:
    assert to_native_symbol("AAPL", "NMS") == "AAPL"
