""""""  #

"""
Copyright (c) 2020-2026, Dany Cajas
All rights reserved.
This work is licensed under BSD 3-Clause "New" or "Revised" License.
License available at https://github.com/dcajasn/Riskfolio-Lib/blob/master/LICENSE.txt
"""

import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

FXMACRODATA_BASE_URL = "https://fxmacrodata.com/api/v1"


def fxmacrodata_release_calendar(
    currency="usd",
    limit=100,
    min_tier=None,
    api_key=None,
    base_url=FXMACRODATA_BASE_URL,
):
    """Get an FXMacroData economic release calendar as a pandas DataFrame."""
    limit = max(1, int(limit))
    params = {"limit": limit}
    token = api_key or os.environ.get("FXMACRODATA_API_KEY")
    if token:
        params["api_key"] = token

    url = f"{base_url.rstrip('/')}/calendar/{currency.lower()}?{urlencode(params)}"
    with urlopen(url, timeout=30) as response:  # nosec B310
        payload = json.loads(response.read().decode("utf-8"))

    events = payload.get("data", [])
    if min_tier is not None:
        events = [
            event
            for event in events
            if int(event.get("market_tier") or 99) <= int(min_tier)
        ]

    df = pd.DataFrame(events[:limit])
    if df.empty:
        return df

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.set_index("date").sort_index()
    if "announcement_datetime" in df.columns:
        df["announcement_datetime"] = pd.to_datetime(
            df["announcement_datetime"], unit="s", utc=True, errors="coerce"
        )
    return df


def fxmacrodata_event_windows(index, events, days_before=1, days_after=1):
    """Return a boolean pandas Series for dates near FXMacroData events."""
    normalized_index = pd.DatetimeIndex(index).normalize()
    mask = pd.Series(False, index=index)
    if events.empty:
        return mask

    event_dates = (
        pd.DatetimeIndex(events.index)
        if isinstance(events.index, pd.DatetimeIndex)
        else pd.to_datetime(events["date"], errors="coerce")
    )
    for event_date in event_dates.dropna().normalize():
        start = event_date - pd.Timedelta(days=days_before)
        end = event_date + pd.Timedelta(days=days_after)
        mask |= (normalized_index >= start) & (normalized_index <= end)
    return mask
