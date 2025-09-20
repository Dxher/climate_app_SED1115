# tests/test_core.py
import numpy as np
import pandas as pd
import pytest
from climate_core import (
    clean_dataframe, compute_station_year, available_months, available_days,
    select_row, groups_for, melt_for_plot, _val, _get
)

def test_clean_dataframe_drops_noise_and_flags(df_small):
    df = clean_dataframe(df_small)
    # noise
    assert "Data Quality" not in df.columns
    # flag suffix
    assert "Some Flag" not in df.columns
    # coerced numbers
    assert df["Max Temp (°C)"].dtype.kind in ("i", "f")
    # em dash -> NaN after coercion
    assert np.isnan(df.loc[df["Day"] == 1, "Total Rain (mm)"]).all()

def test_compute_station_year(df_small):
    df = clean_dataframe(df_small)
    station, year = compute_station_year(df_small)  # you used Year column in the app
    assert station == "Ottawa"
    assert year == 2000

def test_available_months_and_days(df_small):
    df = clean_dataframe(df_small)
    assert available_months(df) == [1]
    assert available_days(df, 1) == [1, 2]

def test_select_row(df_small):
    df = clean_dataframe(df_small)
    row = select_row(df, month=1, day=2)
    assert row is not None
    assert row["Day"] == 2
    assert select_row(df, month=1, day=31) is None  # not present

def test_groups_for(df_small):
    df = clean_dataframe(df_small)
    groups = groups_for(df)
    # Temperature should have 3 columns present
    assert set(groups["Temperature"]["columns"]) == {
        "Max Temp (°C)", "Min Temp (°C)", "Mean Temp (°C)"
    }
    # Wind should include gust speed
    assert groups["Wind"]["columns"] == ["Spd of Max Gust (km/h)"]

def test_melt_for_plot(df_small):
    df = clean_dataframe(df_small)
    month_df = df[df["Month"] == 1].copy()
    y_cols = ["Max Temp (°C)", "Min Temp (°C)", "Mean Temp (°C)"]
    plot_df = melt_for_plot(month_df, y_cols)
    # 2 days * 3 series = 6 rows
    assert plot_df.shape == (6, 3)
    assert set(plot_df.columns) == {"Day", "Series", "Value"}
    # check one known row
    assert ((plot_df["Day"] == 2) & (plot_df["Series"] == "Mean Temp (°C)")).any()

def test_val_and_get_helpers(df_small):
    df = clean_dataframe(df_small)
    row = select_row(df, 1, 1)
    # _get returns actual value
    assert _get(row, "Total Precip (mm)") == 0.0
    # _val formats numbers / handles NaN
    assert _val(3.14159, 2) == "3.14"
    assert _val(np.nan, 1) == "—"
