"""Geographic visualisation for the Glints Job Intel dashboard.

This module renders a simple Folium map of Indonesia with one circle
marker per city in the dataset. The marker radius scales with job count,
and the tooltip surfaces city name, job count, and median salary.

It also exposes :func:`city_summary` — a small grouped DataFrame that
the dashboard shows alongside the map.
"""
from __future__ import annotations

from typing import Final

import folium
import pandas as pd

# ---------------------------------------------------------------------------
# Static reference data
# ---------------------------------------------------------------------------

# Approximate coordinates (latitude, longitude) of major Indonesian cities
# where data-science jobs concentrate. Order is fixed so dashboards render
# deterministically across runs.
CITY_COORDS: Final[dict[str, tuple[float, float]]] = {
    "Jakarta": (-6.2088, 106.8456),
    "Bandung": (-6.9175, 107.6191),
    "Surabaya": (-7.2575, 112.7521),
    "Yogyakarta": (-7.7956, 110.3695),
    "Medan": (3.5952, 98.6722),
    "Semarang": (-6.9667, 110.4167),
    "Makassar": (-5.1477, 119.4327),
    "Denpasar": (-8.6705, 115.2126),
}

INDONESIA_CENTER: Final[tuple[float, float]] = (-2.5, 118.0)
INDONESIA_ZOOM: Final[int] = 5

# CartoDB Positron keeps the basemap calm and lets the data pop.
_DEFAULT_TILES: Final[str] = "CartoDB positron"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def plot_geo_map(df: pd.DataFrame) -> folium.Map:
    """Render a Folium map with one circle marker per Indonesian city."""
    fmap = folium.Map(
        location=list(INDONESIA_CENTER),
        zoom_start=INDONESIA_ZOOM,
        tiles=_DEFAULT_TILES,
        control_scale=True,
    )

    summary = _city_aggregates(df)
    if summary.empty:
        # Empty-state: just return the map centred on Indonesia.
        return fmap

    max_count = max(int(summary["count"].max()), 1)

    for _, row in summary.iterrows():
        city = str(row["city_clean"])
        if city not in CITY_COORDS:
            # Skip cities we don't have coordinates for.
            continue
        lat, lon = CITY_COORDS[city]
        count = int(row["count"])
        median_salary = float(row["median_salary"])
        top_role = str(row["top_role"])

        radius = 6.0 + 18.0 * (count / max_count) ** 0.5
        tooltip_html = (
            f"<b>{city}</b><br>"
            f"Jobs: {count:,}<br>"
            f"Median salary: Rp {median_salary / 1e6:.1f}M<br>"
            f"Top role: {top_role}"
        )

        # Colour by count: light for fewer, deep green for more.
        shade = count / max_count
        colour = ["#c7e9c0", "#74c476", "#1b6b3a"][min(2, int(shade * 3))]

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            # Lighter teal so the stroke stays visible against the dark
            # slate dashboard canvas; the previous deep green blended
            # into the background at night/dark theme.
            color="#5EEAD4",
            weight=1,
            fill=True,
            fill_color=colour,
            fill_opacity=0.85,
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
            popup=folium.Popup(tooltip_html, max_width=300),
        ).add_to(fmap)

    return fmap


def city_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return per-city summary (count, median salary, remote %, top role)."""
    return _city_aggregates(df).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _city_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Group df by city and compute per-city summary columns (pandas groupby)."""
    if df.empty or "city_clean" not in df.columns:
        return pd.DataFrame(
            columns=["city_clean", "count", "median_salary", "remote_pct", "top_role"]
        )
    work = df.copy()
    work["salary_num"] = pd.to_numeric(work.get("salary_avg", pd.Series(dtype=float)), errors="coerce")
    # Derive the remote flag from ``workplace_type`` (canonical source of
    # truth) so the aggregation works regardless of whether the upstream
    # pipeline exposed a separate ``is_remote`` boolean.
    if "workplace_type" in work.columns:
        work["_is_remote"] = work["workplace_type"].astype(str).str.lower() == "remote"
    else:
        work["_is_remote"] = pd.Series([False] * len(work), index=work.index)

    g = work.groupby("city_clean", dropna=False)
    out = g.agg(
        count=("city_clean", "size"),
        median_salary=("salary_num", "median"),
        remote_pct=("_is_remote", lambda s: float(s.astype(bool).mean()) * 100.0),
        top_role=(
            "keyword",
            lambda s: s.dropna().astype(str).value_counts().index[0]
            if not s.dropna().empty
            else "n/a",
        ),
    ).reset_index()
    return out.sort_values("count", ascending=False).reset_index(drop=True)


__all__ = ["CITY_COORDS", "city_summary", "plot_geo_map"]
