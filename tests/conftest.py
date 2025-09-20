# tests/conftest.py
import pandas as pd
import pytest

@pytest.fixture
def df_small():
    data = {
        "Station Name": ["Ottawa", "Ottawa"],
        "Year": [2000, 2000],
        "Month": [1, 1],
        "Day": [1, 2],
        "Max Temp (°C)": ["-5.0", "0.0"],        # strings on purpose to test coercion
        "Min Temp (°C)": ["-12.3", "-8.0"],
        "Mean Temp (°C)": ["-8.6", "-4.0"],
        "Total Rain (mm)": ["—", "1.2"],         # em dash should become NaN
        "Total Precip (mm)": ["0", "1.2"],
        "Total Snow (cm)": ["3", "0"],
        "Snow on Grnd (cm)": ["9", "8"],
        "Spd of Max Gust (km/h)": ["25", "30"],
        "Dir of Max Gust (10s deg)": ["12", "18"],
        "Data Quality": ["X", "X"],              # noise
        "Some Flag": ["Y", "N"],                 # flag suffix column
    }
    return pd.DataFrame(data)
