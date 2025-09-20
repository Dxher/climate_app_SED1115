
# climate_core.py
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import List, Tuple

DROP_NOISE = {
    "Climate ID", "Data Quality", "Longitude (x)", "Latitude (y)",
    "Heat Deg Days (°C)", "Cool Deg Days (°C)"
}

NON_NUMERIC_DEFAULT = {"Station Name", "Date/Time"}  # keep these as strings

def clean_dataframe(
    df: pd.DataFrame,
    drop_noise: set[str] = DROP_NOISE,
    non_numeric: set[str] = NON_NUMERIC_DEFAULT,
    flag_suffix: str = "Flag",
) -> pd.DataFrame:
    """Mirror your cleaning: drop noise + *Flag columns, coerce numerics."""
    # drop explicit unwanted columns
    to_drop = [c for c in drop_noise if c in df.columns]
    # drop any column that ends with the suffix e.g., "...Flag"
    to_drop += [c for c in df.columns if c.endswith(flag_suffix)]
    df = df.drop(columns=to_drop, errors="ignore").copy()

    # coerce object columns to numeric, except listed non-numeric ones
    obj_cols = df.select_dtypes(include="object").columns.difference(non_numeric)
    df[obj_cols] = df[obj_cols].apply(pd.to_numeric, errors="coerce")
    return df

def compute_station_year(df: pd.DataFrame) -> Tuple[str, int | None]:
    """Return display-friendly (station_name, year_value)."""
    if "Station Name" in df.columns and df["Station Name"].notna().any():
        station = str(df["Station Name"].dropna().iat[0])
    else:
        station = "Station"

    year = None
    if "Year" in df.columns and df["Year"].notna().any():
        year = int(pd.to_numeric(df["Year"], errors="coerce").dropna().iat[0])
    elif "Date/Time" in df.columns:
        # If you ever keep Date/Time instead of Year
        y = pd.to_datetime(df["Date/Time"], errors="coerce").dt.year.dropna()
        if not y.empty:
            year = int(y.iat[0])
    return station, year

def available_months(df: pd.DataFrame) -> List[int]:
    return sorted(pd.Series(df.get("Month", pd.Series(dtype="float64"))).dropna().astype(int).unique().tolist())

def available_days(df: pd.DataFrame, month: int) -> List[int]:
    return sorted(df.loc[df["Month"] == month, "Day"].dropna().astype(int).unique().tolist())

def select_row(df: pd.DataFrame, month: int, day: int) -> pd.Series | None:
    sel = df[(df["Month"] == month) & (df["Day"] == day)]
    return sel.iloc[0] if not sel.empty else None

def existing_columns(df: pd.DataFrame, candidates: List[str]) -> List[str]:
    return [c for c in candidates if c in df.columns]

def groups_for(df: pd.DataFrame) -> dict:
    return {
        "Temperature": {
            "columns": existing_columns(df, ["Max Temp (°C)", "Min Temp (°C)", "Mean Temp (°C)"]),
            "y_title": "Temperature (°C)",
        },
        "Precipitation": {
            "columns": existing_columns(df, ["Total Rain (mm)", "Total Precip (mm)"]),
            "y_title": "Precipitation (mm)",
        },
        "Snow": {
            "columns": existing_columns(df, ["Total Snow (cm)", "Snow on Grnd (cm)"]),
            "y_title": "Snow (cm)",
        },
        "Wind": {
            "columns": existing_columns(df, ["Spd of Max Gust (km/h)"]),
            "y_title": "Wind (km/h)",
        },
    }

def melt_for_plot(month_df: pd.DataFrame, y_cols: List[str]) -> pd.DataFrame:
    if not y_cols:
        return pd.DataFrame(columns=["Day", "Series", "Value"])
    return month_df[["Day"] + y_cols].melt(
        id_vars="Day", value_vars=y_cols, var_name="Series", value_name="Value"
    )

def _val(value, decimals: int = 1) -> str:
    return (f"{value:.{decimals}f}" if pd.notna(value) and np.isfinite(value) else "—")

def _get(row: pd.Series | None, name: str, default=np.nan):
    return row.get(name, default) if row is not None else default
