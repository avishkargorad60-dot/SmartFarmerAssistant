from agents.market_price_agent import market_price_agent as mpa


def test_market_agent_filters_inconsistent_state_response_locally(monkeypatch):
    """A successful but wrong server-side state filter must not leak other states."""
    responses = iter([
        {
            "success": True,
            "records": [
                {"commodity": "Wheat", "state": "Maharashtra", "market": "Wrong"}
            ],
            "error": None,
        },
        {
            "success": True,
            "records": [
                {
                    "commodity": "Wheat",
                    "state": "Gujarat",
                    "district": "Amreli",
                    "market": "APMC Bagasara",
                    "modal_price": "2725",
                    "arrival_date": "21/09/2026",
                }
            ],
            "error": None,
        },
    ])
    calls = []

    def government_prices(crop, state=None):
        calls.append((crop, state))
        return next(responses)

    monkeypatch.setattr(mpa, "get_government_prices", government_prices)

    result = mpa.get_market_prices("wheat", "gujarat")

    assert calls == [("wheat", "gujarat"), ("wheat", None)]
    assert result["source"] == "government"
    assert result["count"] == 1
    assert result["data"][0]["market"] == "APMC Bagasara"


def test_market_agent_uses_demo_only_after_government_failure(monkeypatch):
    monkeypatch.setattr(
        mpa,
        "get_government_prices",
        lambda crop, state=None: {
            "success": False,
            "records": [],
            "error": "network error",
        },
    )

    result = mpa.get_market_prices("Maize", "Maharashtra")

    assert result["source"] == "local_demo"
    assert result["count"] >= 1
    assert "unavailable" in result["note"].lower()


def test_market_agent_returns_government_no_state_match_without_fallback(monkeypatch):
    records = [{"commodity": "Wheat", "state": "Punjab", "market": "Amritsar"}]
    monkeypatch.setattr(
        mpa,
        "get_government_prices",
        lambda crop, state=None: {"success": True, "records": records, "error": None},
    )

    result = mpa.get_market_prices("Wheat", "Gujarat")

    assert result["source"] == "government_no_state_match"
    assert result["data"][0]["state"] == "Punjab"
