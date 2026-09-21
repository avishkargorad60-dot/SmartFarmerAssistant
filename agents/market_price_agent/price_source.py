def find_prices(data, crop, state):
    """
    Find market-price records matching a crop and state.
    """

    results = []

    for record in data:
        commodity = str(
            record.get("commodity", "")
        ).strip().lower()

        record_state = str(
            record.get("state", "")
        ).strip().lower()

        if (
            commodity == crop.strip().lower()
            and record_state == state.strip().lower()
        ):
            results.append(record)

    return results