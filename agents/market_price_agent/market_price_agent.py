import os
import json
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

from .price_source import find_prices

# Resolve the same project .env as Flask. Deployment environment values are
# preserved, and the key itself is never logged.
PROJECT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(PROJECT_ENV_PATH, override=False)


# ============================================================
# GOVERNMENT OF INDIA DATA.GOV.IN API
# ============================================================

DATA_GOV_URL = (
    "https://api.data.gov.in/resource/"
    "9ef84268-d588-465a-a308-a864a43d0070"
)


# ============================================================
# GOVERNMENT API FUNCTION
# ============================================================

def get_government_prices(crop, state=None):
    """
    Fetch latest available mandi prices from
    Government of India data.gov.in.

    Returns:
        {
            "success": True/False,
            "records": [...],
            "error": None or message
        }
    """

    api_key = os.getenv("DATA_GOV_API_KEY")

    if not api_key:
        print("DATA_GOV_API_KEY not found.")
        return {
            "success": False,
            "records": [],
            "error": "DATA_GOV_API_KEY not configured.",
            "configuration_error": True,
        }

    params = {
        "api-key": api_key,
        "format": "json",
        # Verify state matches locally below because the API's state filter is
        # inconsistent; this fetches a useful batch of current crop records.
        "limit": "1000",
        "filters[commodity]": crop,
    }

    # Add state filter only when state is provided
    if state:
        params["filters[state.keyword]"] = state

    try:

        # ----------------------------------------------------
        # USE CURL
        # ----------------------------------------------------

        if shutil.which("curl.exe"):

            command = [
                "curl.exe",
                "-sS",
                "--max-time",
                "60",
                "-G",
                DATA_GOV_URL,
            ]

            for key, value in params.items():
                command.extend([
                    "--data-urlencode",
                    f"{key}={value}"
                ])

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=70
            )

            if result.returncode != 0:

                print("Government API request failed.")

                if result.stderr:
                    print(
                        "Error:",
                        result.stderr.strip()
                    )

                return {
                    "success": False,
                    "records": [],
                    "error": "Government API request failed."
                }

            payload = result.stdout

        # ----------------------------------------------------
        # PYTHON FALLBACK
        # ----------------------------------------------------

        else:

            query = urllib.parse.urlencode(params)

            url = f"{DATA_GOV_URL}?{query}"

            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json"
                }
            )

            with urllib.request.urlopen(
                req,
                timeout=60
            ) as response:

                payload = response.read().decode(
                    "utf-8"
                )

        # ----------------------------------------------------
        # PARSE JSON
        # ----------------------------------------------------

        if not payload.strip():

            return {
                "success": False,
                "records": [],
                "error": "Government API returned empty response."
            }

        data = json.loads(payload)

        records = data.get(
            "records",
            []
        )

        total = data.get(
            "total",
            len(records)
        )

        print(
            f"Government API response: "
            f"{total} matching records."
        )

        # IMPORTANT:
        # Zero records does NOT mean API failure.

        return {
            "success": True,
            "records": records,
            "error": None
        }

    except subprocess.TimeoutExpired:

        print("Government API request timed out.")

        return {
            "success": False,
            "records": [],
            "error": "Government API request timed out."
        }

    except urllib.error.URLError as exc:

        print(
            f"Government API request failed: {exc}"
        )

        return {
            "success": False,
            "records": [],
            "error": str(exc)
        }

    except json.JSONDecodeError:

        print(
            "Government API returned invalid JSON."
        )

        return {
            "success": False,
            "records": [],
            "error": "Invalid JSON response."
        }

    except Exception as exc:

        print(
            f"Government API error: {exc}"
        )

        return {
            "success": False,
            "records": [],
            "error": str(exc)
        }


# ============================================================
# FORMAT GOVERNMENT RECORDS
# ============================================================

def format_results(records):

    results = []

    for record in records:

        results.append({

            "state": record.get(
                "state",
                ""
            ),

            "district": record.get(
                "district",
                ""
            ),

            "market": record.get(
                "market",
                ""
            ),

            "commodity": record.get(
                "commodity",
                ""
            ),

            "variety": record.get(
                "variety",
                ""
            ),

            "grade": record.get(
                "grade",
                ""
            ),

            "arrival_date": record.get(
                "arrival_date",
                ""
            ),

            "min_price": record.get(
                "min_price"
            ),

            "max_price": record.get(
                "max_price"
            ),

            "modal_price": record.get(
                "modal_price"
            ),

            "source": (
                "Government of India - data.gov.in"
            )
        })

    return results


def _normalise_state(value):
    """Compare state labels despite case, whitespace, or punctuation changes."""
    return "".join(
        char for char in str(value or "").casefold() if char.isalnum()
    )


def _records_for_state(records, state):
    """Return only API records whose state truly matches the requested state."""
    requested_state = _normalise_state(state)
    return [
        record
        for record in records
        if _normalise_state(record.get("state")) == requested_state
    ]


# ============================================================
# MAIN MARKET PRICE FUNCTION
# ============================================================

def get_market_prices(crop, state):

    print(
        f"\nSearching market prices "
        f"for {crop} in {state}..."
    )

    # Ask for the state first, but verify every record locally: data.gov.in's
    # server-side state filter has intermittently returned inconsistent data.

    government_result = get_government_prices(
        crop,
        state
    )

    # A missing key is an application configuration issue, not a failed
    # government request.  Do not mask it with local demo data.
    if government_result.get("configuration_error"):
        return {
            "source": "configuration_error",
            "data": [],
            "count": 0,
            "note": (
                "Live market prices are unavailable because "
                "DATA_GOV_API_KEY is not configured for the backend."
            ),
        }

    # --------------------------------------------------------
    # LIVE GOVERNMENT DATA FOUND
    # --------------------------------------------------------

    if government_result["success"]:

        records = _records_for_state(
            government_result["records"], state
        )

        if records:

            formatted_records = format_results(
                records
            )

            print(
                f"Found {len(formatted_records)} "
                f"government records."
            )

            return {
                "source": "government",
                "data": formatted_records,
                "count": len(formatted_records),
                "note": (
                    "Latest available daily mandi "
                    "prices from Government of India."
                )
            }

        # ====================================================
        # API WORKED BUT NO STATE RECORDS
        # ====================================================

        print(
            f"No current government records "
            f"found for {crop} in {state}."
        )

        # ----------------------------------------------------
        # 2. Fetch current crop records without the unreliable state filter,
        #    then filter the returned records locally.
        # ----------------------------------------------------

        print(
            f"Checking current India-wide "
            f"records for {crop}..."
        )

        national_result = get_government_prices(
            crop
        )

        if national_result["success"]:

            national_records = national_result["records"]
            matching_records = _records_for_state(national_records, state)

            if matching_records:
                formatted_records = format_results(matching_records)
                print(
                    f"Found {len(formatted_records)} government records "
                    "after local state filtering."
                )
                return {
                    "source": "government",
                    "data": formatted_records,
                    "count": len(formatted_records),
                    "note": (
                        "Latest available daily mandi prices from Government "
                        "of India (state matched locally)."
                    )
                }

            if national_records:

                formatted_records = format_results(
                    national_records
                )

                states = sorted(
                    set(
                        record.get(
                            "state",
                            ""
                        )
                        for record in formatted_records
                        if record.get("state")
                    )
                )

                state_text = ", ".join(
                    states
                )

                return {
                    "source": "government_no_state_match",

                    "data": formatted_records,

                    "count": len(
                        formatted_records
                    ),

                    "requested_state": state,

                    "available_states": states,

                    "note": (
                        f"No current government records "
                        f"were found for {crop} in {state}. "
                        f"Current records were found in: "
                        f"{state_text}."
                    )
                }

        # ====================================================
        # API SUCCESSFUL, BUT NO RECORDS AT ALL
        # ====================================================

        return {
            "source": "government_no_records",

            "data": [],

            "count": 0,

            "requested_state": state,

            "note": (
                f"The Government of India API responded "
                f"successfully, but no current records "
                f"were found for {crop}."
            )
        }

    # ========================================================
    # API ACTUALLY FAILED
    # ========================================================

    print(
        "Government API unavailable."
    )

    # ========================================================
    # OPTIONAL LOCAL DEMO FALLBACK
    # ========================================================

    print(
        "Checking local demo data..."
    )

    local_path = os.path.join(
        os.path.dirname(__file__),
        "local_market_data.json"
    )

    try:

        with open(
            local_path,
            "r",
            encoding="utf-8"
        ) as f:

            dataset = json.load(f)

    except Exception:

        dataset = []

    filtered = (
        find_prices(
            dataset,
            crop,
            state
        )
        if dataset
        else []
    )

    if filtered:

        return {
            "source": "local_demo",

            "data": filtered,

            "count": len(filtered),

            "note": (
                "Government API was unavailable. "
                "These are local demo prices and "
                "are NOT live government prices."
            )
        }

    return {
        "source": "none",

        "data": [],

        "count": 0,

        "note": (
            "Government API unavailable and "
            "no local demo data was found."
        )
    }


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(result):

    if not result:

        print(
            "\n❌ No result returned."
        )

        return

    records = result.get(
        "data",
        []
    )

    print(
        f"\nRecords found: {len(records)}"
    )

    print(
        f"Source: {result.get('source', 'unknown')}"
    )

    print(
        f"Note: {result.get('note', '')}"
    )

    print(
        "-" * 70
    )

    if not records:

        print(
            "No market records available."
        )

        return

    for i, record in enumerate(
        records,
        start=1
    ):

        print(
            f"\n{i}. "
            f"{record.get('market', 'Unknown Market')}"
        )

        print(
            f"   District  : "
            f"{record.get('district', 'N/A')}"
        )

        print(
            f"   State     : "
            f"{record.get('state', 'N/A')}"
        )

        print(
            f"   Commodity : "
            f"{record.get('commodity', 'N/A')}"
        )

        print(
            f"   Variety   : "
            f"{record.get('variety', 'N/A')}"
        )

        print(
            f"   Min Price : "
            f"₹{record.get('min_price', 'N/A')}"
        )

        print(
            f"   Max Price : "
            f"₹{record.get('max_price', 'N/A')}"
        )

        print(
            f"   Modal     : "
            f"₹{record.get('modal_price', 'N/A')}"
        )

        print(
            f"   Date      : "
            f"{record.get('arrival_date', 'N/A')}"
        )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print(
        "\n💰 SMART FARMER - MARKET PRICE AGENT"
    )

    print(
        "------------------------------------"
    )

    crop = input(
        "Enter crop: "
    ).strip()

    state = input(
        "Enter state: "
    ).strip()

    if not crop:

        print(
            "\n❌ Crop is required."
        )

        return

    if not state:

        print(
            "\n❌ State is required."
        )

        return

    result = get_market_prices(
        crop,
        state
    )

    display_results(
        result
    )


if __name__ == "__main__":

    main()
