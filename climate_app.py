# climate_app.py
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st


# Load the CSV file into a dataframe
file_path = 'en_climate_daily_ON_6105976_2000_P1D.csv'
df = pd.read_csv(file_path)

# Drop all columns ending with "Flag"
flag_cols = [col for col in df.columns if col.endswith("Flag")]

# Drop specific columns
cols_to_drop = [
    "Climate ID", "Data Quality", "Longitude (x)",
    "Latitude (y)", "Heat Deg Days (°C)", "Cool Deg Days (°C)"
]

# initialize smaller db
df = df.drop(columns=cols_to_drop + flag_cols, errors="ignore")

# Ensure columns are numeric
# prevents numbers as strings (e.g., "3.4", "—", "M").
for col in df.columns:
    if col not in ["Station Name", "Date/Time"] and df[col].dtype == "object":
        df[col] = pd.to_numeric(df[col], errors="coerce") #Make errors NaN (typically letters or empty spaces)

# Convenience: unique station & year
station_name = str(df["Station Name"].dropna().unique()[0]) if "Station Name" in df.columns else "Station"
year_value = int(df["Year"].dropna().unique()[0]) if "Year" in df.columns else int(df["Date/Time"].dt.year.mode()[0])

# ------------------------
# UI
# ------------------------
st.set_page_config(page_title="Climate Viewer", layout="centered") #or wide

# Header 
st.markdown(
    f"<h2 style='text-align:center;margin-top:0'>{station_name}'s climate in the year {year_value}</h2>",
    unsafe_allow_html=True, #Streamlit option to render HTML instead of reading the text as text 
)

st.markdown(
    f"<h3 style='text-align:left;margin-top:0'>Select a day:</h3>",
    unsafe_allow_html=True, #Streamlit option to render HTML instead of reading the text as text 
)

# Month & Day drop down boxes
months_available = sorted(df["Month"].dropna().unique().astype(int).tolist()) #sort list, remove missing values (NaN), keep one of each month, ensure ints, convert array to list.
col_month, col_day = st.columns([1, 1]) # variable references to streamlit column containers

with col_month:
    month = st.selectbox("Month", months_available, format_func=lambda m: f"{m:02d}")

days_available = sorted(df.loc[df["Month"] == month, "Day"].dropna().unique().astype(int).tolist())
with col_day:
    if days_available:
        day = st.selectbox("Day", days_available, format_func=lambda d: f"{d:02d}")
    else:
        day = None
        st.warning("No days available for this month in the dataset.")

# Row for the selected date
row_sel = None
if day is not None:
    row = df[(df["Month"] == month) & (df["Day"] == day)]
    row_sel = row.iloc[0] if not row.empty else None

# Category selector
labels = ["🌡️ Temperature", "🌧️ Precipitation", "❄️ Snow", "💨 Wind"]
picked = st.radio("Data category", labels, horizontal=True)
category = picked.split(" ", 1)[1]   # Splits the labels

# ------------------------
# Column groupings per category
# ------------------------
groups = {
    "Temperature": {
        "columns": [c for c in ["Max Temp (°C)", "Min Temp (°C)", "Mean Temp (°C)"] if c in df.columns], #make a column for each list item if they're in df.columns (the df headers)
        "y_title": "Temperature (°C)"
    },
    "Precipitation": {
        "columns": [c for c in ["Total Rain (mm)", "Total Precip (mm)"] if c in df.columns],
        "y_title": "Precipitation (mm)"
    },
    "Snow": {
        "columns": [c for c in ["Total Snow (cm)", "Snow on Grnd (cm)"] if c in df.columns],
        "y_title": "Snow (cm)"
    },
    "Wind": {
        "columns": [c for c in ["Spd of Max Gust (km/h)"] if c in df.columns],
        "y_title": "Wind (km/h)"
    },
}

y_cols = groups[category]["columns"]
y_axis_title = groups[category]["y_title"]

# ---- Helpers ----
def _val(v, decimals=1):
    """Format a numeric value or return '—' if missing."""
    return (f"{v:.{decimals}f}" if pd.notna(v) and np.isfinite(v) else "—")

def _get(row, name, default=np.nan):
    """Safely get a value from a Series/row."""
    return row.get(name, default) if row is not None else default


# ---- Selected-day metrics by category ----
if category == "Temperature":
    col_a, col_b, col_c = st.columns(3)

    max_t  = _get(row_sel, "Max Temp (°C)")
    min_t  = _get(row_sel, "Min Temp (°C)")
    mean_t = _get(row_sel, "Mean Temp (°C)")

    col_a.metric("Max Temp (°C)",  _val(max_t))
    col_b.metric("Min Temp (°C)",  _val(min_t))
    col_c.metric("Mean Temp (°C)", _val(mean_t))

elif category == "Precipitation":
    col_a, col_b = st.columns(2)

    rain   = _get(row_sel, "Total Rain (mm)")
    precip = _get(row_sel, "Total Precip (mm)")

    col_a.metric("Total Rain (mm)",   _val(rain))
    col_b.metric("Total Precip (mm)", _val(precip))

elif category == "Snow":
    col_a, col_b = st.columns(2)

    snow_total = _get(row_sel, "Total Snow (cm)")
    snow_grnd  = _get(row_sel, "Snow on Grnd (cm)")

    col_a.metric("Total Snow (cm)",    _val(snow_total))
    col_b.metric("Snow on Grnd (cm)",  _val(snow_grnd))

elif category == "Wind":
    # Show speed; optionally direction if present in your dataset
    has_dir = "Dir of Max Gust (10s deg)" in df.columns

    if has_dir:
        col_a, col_b = st.columns(2)
    else:
        col_a = st.columns(1)[0]

    gust_spd = _get(row_sel, "Spd of Max Gust (km/h)")
    col_a.metric("Max Gust Speed (km/h)", _val(gust_spd))

    if has_dir:
        gust_dir = _get(row_sel, "Dir of Max Gust (10s deg)")
        # Direction is categorical-ish; display as an integer (no decimals)
        col_b.metric("Max Gust Dir (10s deg)", _val(gust_dir, decimals=0))


# ------------------------
# Chart for the selected month across days
# ------------------------

#filters months, copy's the list to potentially avoid chained-assignment warnings, and sorts days
month_df = df[df["Month"] == month].copy().sort_values("Day")

# If no columns for this category exist (Temp/Precip/Snow/Wind), inform the user
if not y_cols:
    st.error(f"No columns found for {category} in this dataset.")

else:
    # Selects only the X axis (Day) plus the Y series you want. Melt compresses the columns into Day Series and Value instead of having multiple columns. Good for plotly
    plot_df = month_df[["Day"] + y_cols].melt(id_vars="Day", value_vars=y_cols,
                                              var_name="Series", value_name="Value")

    # Plotly line chart
    fig = px.line(
        plot_df,
        x="Day",
        y="Value",
        color="Series",
        markers=True,
        title=f"{category} for {station_name} in {year_value}-{month:02d}",
    )
    fig.update_layout(
        xaxis_title="Day of Month",
        yaxis_title=y_axis_title,
        legend_title="",
        margin=dict(l=10, r=10, t=40, b=10),
    )

    # Highlight the selected day (vertical ruler)
    if day is not None and len(month_df):
        fig.add_vline(x=day, line_dash="dash", annotation_text=f"Day {day}", annotation_position="top")

    #Display chart
    st.plotly_chart(fig, use_container_width=True)

# ------------------------
# show the selected-day record for reference
# ------------------------
with st.expander("Selected day - full record"):
    if row_sel is not None:
        # Pretty print the row
        show = row_sel.drop(labels=[c for c in row_sel.index if "Unnamed:" in c], errors="ignore")
        st.dataframe(show.to_frame(name="Value"))
    else:
        st.write("No record found for this date.")

