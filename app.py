"""
Real Exchange Rate App
----------------------
Streamlit app that downloads monthly CPI and exchange-rate data from the IMF
SDMX 3.0 API and computes the bilateral real exchange rate between two countries.

Definitions (Country 1 = home, Country 2 = foreign)
    S(t)   = units of Country 2 currency per 1 unit of Country 1 currency
           = (Country 2 LCU per USD) / (Country 1 LCU per USD)
    P1(t)  = Country 1 monthly CPI
    P2(t)  = Country 2 monthly CPI
    RER(t) = S(t) * P1(t) / P2(t)
    RER*   = average of RER(t) over valid months in the selected sample
    Real Index(t) = 100 * RER(t) / RER*
"""

import io
import time

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
IMF_BASE = "https://api.imf.org/external/sdmx/3.0"
AGENCY = "IMF.STA"
CPI_FLOW = "CPI"
FX_FLOW = "ER"
START_PERIOD = "1976-01"
CPI_KEY = "{iso}.CPI._T.IX.M"        # monthly CPI, all items, index
FX_KEY = "{iso}.XDC_USD.PA_RT.M"     # monthly avg, local currency per USD

# Countries: display name -> IMF code (ISO3; the IMF uses G163 for the Euro area)
COUNTRIES = {
    "Euro area": "G163",
    'Afghanistan': "AFG",
    'Albania': "ALB",
    'Algeria': "DZA",
    'Angola': "AGO",
    'Antigua and Barbuda': "ATG",
    'Argentina': "ARG",
    'Armenia': "ARM",
    'Aruba': "ABW",
    'Australia': "AUS",
    'Austria': "AUT",
    'Azerbaijan': "AZE",
    'Bahamas': "BHS",
    'Bahrain': "BHR",
    'Bangladesh': "BGD",
    'Barbados': "BRB",
    'Belarus': "BLR",
    'Belgium': "BEL",
    'Belize': "BLZ",
    'Benin': "BEN",
    'Bhutan': "BTN",
    'Bolivia': "BOL",
    'Bosnia and Herzegovina': "BIH",
    'Botswana': "BWA",
    'Brazil': "BRA",
    'Brunei Darussalam': "BRN",
    'Bulgaria': "BGR",
    'Burkina Faso': "BFA",
    'Burundi': "BDI",
    'Cabo Verde': "CPV",
    'Cambodia': "KHM",
    'Cameroon': "CMR",
    'Canada': "CAN",
    'Central African Republic': "CAF",
    'Chad': "TCD",
    'Chile': "CHL",
    'China': "CHN",
    'Colombia': "COL",
    'Comoros': "COM",
    'Congo, Dem. Rep.': "COD",
    'Congo, Rep.': "COG",
    'Costa Rica': "CRI",
    'Croatia': "HRV",
    'Curaçao': "CUW",
    'Cyprus': "CYP",
    'Czech Republic': "CZE",
    "Côte d'Ivoire": "CIV",
    'Denmark': "DNK",
    'Djibouti': "DJI",
    'Dominica': "DMA",
    'Dominican Republic': "DOM",
    'Ecuador': "ECU",
    'Egypt': "EGY",
    'El Salvador': "SLV",
    'Equatorial Guinea': "GNQ",
    'Eritrea': "ERI",
    'Estonia': "EST",
    'Eswatini': "SWZ",
    'Ethiopia': "ETH",
    'Fiji': "FJI",
    'Finland': "FIN",
    'France': "FRA",
    'Gabon': "GAB",
    'Gambia': "GMB",
    'Georgia': "GEO",
    'Germany': "DEU",
    'Ghana': "GHA",
    'Greece': "GRC",
    'Grenada': "GRD",
    'Guatemala': "GTM",
    'Guinea': "GIN",
    'Guinea-Bissau': "GNB",
    'Guyana': "GUY",
    'Haiti': "HTI",
    'Honduras': "HND",
    'Hong Kong SAR': "HKG",
    'Hungary': "HUN",
    'Iceland': "ISL",
    'India': "IND",
    'Indonesia': "IDN",
    'Iran': "IRN",
    'Iraq': "IRQ",
    'Ireland': "IRL",
    'Israel': "ISR",
    'Italy': "ITA",
    'Jamaica': "JAM",
    'Japan': "JPN",
    'Jordan': "JOR",
    'Kazakhstan': "KAZ",
    'Kenya': "KEN",
    'Kiribati': "KIR",
    'Korea, Republic of': "KOR",
    'Kosovo': "XKX",
    'Kuwait': "KWT",
    'Kyrgyzstan': "KGZ",
    'Lao P.D.R.': "LAO",
    'Latvia': "LVA",
    'Lebanon': "LBN",
    'Lesotho': "LSO",
    'Liberia': "LBR",
    'Libya': "LBY",
    'Lithuania': "LTU",
    'Luxembourg': "LUX",
    'Macao SAR': "MAC",
    'Madagascar': "MDG",
    'Malawi': "MWI",
    'Malaysia': "MYS",
    'Maldives': "MDV",
    'Mali': "MLI",
    'Malta': "MLT",
    'Marshall Islands': "MHL",
    'Mauritania': "MRT",
    'Mauritius': "MUS",
    'Mexico': "MEX",
    'Micronesia': "FSM",
    'Moldova': "MDA",
    'Mongolia': "MNG",
    'Montenegro': "MNE",
    'Morocco': "MAR",
    'Mozambique': "MOZ",
    'Myanmar': "MMR",
    'Namibia': "NAM",
    'Nauru': "NRU",
    'Nepal': "NPL",
    'Netherlands': "NLD",
    'New Zealand': "NZL",
    'Nicaragua': "NIC",
    'Niger': "NER",
    'Nigeria': "NGA",
    'North Macedonia': "MKD",
    'Norway': "NOR",
    'Oman': "OMN",
    'Pakistan': "PAK",
    'Palau': "PLW",
    'Panama': "PAN",
    'Papua New Guinea': "PNG",
    'Paraguay': "PRY",
    'Peru': "PER",
    'Philippines': "PHL",
    'Poland': "POL",
    'Portugal': "PRT",
    'Qatar': "QAT",
    'Romania': "ROU",
    'Russian Federation': "RUS",
    'Rwanda': "RWA",
    'Saint Kitts and Nevis': "KNA",
    'Saint Lucia': "LCA",
    'Saint Vincent and the Grenadines': "VCT",
    'Samoa': "WSM",
    'San Marino': "SMR",
    'Sao Tome and Principe': "STP",
    'Saudi Arabia': "SAU",
    'Senegal': "SEN",
    'Serbia': "SRB",
    'Seychelles': "SYC",
    'Sierra Leone': "SLE",
    'Singapore': "SGP",
    'Slovakia': "SVK",
    'Slovenia': "SVN",
    'Solomon Islands': "SLB",
    'Somalia': "SOM",
    'South Africa': "ZAF",
    'South Sudan': "SSD",
    'Spain': "ESP",
    'Sri Lanka': "LKA",
    'Sudan': "SDN",
    'Suriname': "SUR",
    'Sweden': "SWE",
    'Switzerland': "CHE",
    'Syria': "SYR",
    'Tajikistan': "TJK",
    'Tanzania': "TZA",
    'Thailand': "THA",
    'Timor-Leste': "TLS",
    'Togo': "TGO",
    'Tonga': "TON",
    'Trinidad and Tobago': "TTO",
    'Tunisia': "TUN",
    'Turkmenistan': "TKM",
    'Tuvalu': "TUV",
    'Türkiye': "TUR",
    'Uganda': "UGA",
    'Ukraine': "UKR",
    'United Arab Emirates': "ARE",
    'United Kingdom': "GBR",
    'United States': "USA",
    'Uruguay': "URY",
    'Uzbekistan': "UZB",
    'Vanuatu': "VUT",
    'Venezuela': "VEN",
    'Vietnam': "VNM",
    'Yemen': "YEM",
    'Zambia': "ZMB",
    'Zimbabwe': "ZWE",
}


# ---------------------------------------------------------------------------
# IMF download helpers
# ---------------------------------------------------------------------------
def _parse_period(p: str) -> pd.Timestamp:
    """Convert IMF period strings such as '1976-M01', '1976-01', '1976M01' to a month start date."""
    p = str(p).strip().replace("-M", "-").replace("M", "-")
    return pd.Period(p[:7], freq="M").to_timestamp()


def _parse_sdmx_json(payload: dict) -> pd.Series:
    data = payload.get("data", payload)
    structure = data["structures"][0] if "structures" in data else data["structure"]
    obs_dims = structure["dimensions"]["observation"]
    time_dim = next((d for d in obs_dims if d.get("id") == "TIME_PERIOD"), obs_dims[0])
    time_pos = obs_dims.index(time_dim)
    periods = [v.get("id", v.get("value")) for v in time_dim["values"]]

    values = {}
    for dataset in data.get("dataSets", []):
        for series in dataset.get("series", {}).values():
            for obs_key, obs in series.get("observations", {}).items():
                idx = int(str(obs_key).split(":")[time_pos])
                val = obs[0] if isinstance(obs, list) else obs
                if val in (None, "", "NaN"):
                    continue
                values[_parse_period(periods[idx])] = float(val)
    return pd.Series(values, dtype="float64").sort_index()


def _parse_sdmx_csv(text: str) -> pd.Series:
    df = pd.read_csv(io.StringIO(text))
    df = df.dropna(subset=["OBS_VALUE"])
    s = pd.Series(
        pd.to_numeric(df["OBS_VALUE"], errors="coerce").values,
        index=[_parse_period(p) for p in df["TIME_PERIOD"]],
    )
    return s.dropna().groupby(level=0).last().sort_index()


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def fetch_imf_series(flow: str, key: str) -> pd.Series:
    """Download one monthly IMF series. Returns an empty Series if unavailable."""
    url = f"{IMF_BASE}/data/dataflow/{AGENCY}/{flow}/+/{key}"
    attempts = [
        ("json", {"Accept": "application/vnd.sdmx.data+json;version=2.0.0"}),
        ("csv", {"Accept": "application/vnd.sdmx.data+csv;version=2.0.0"}),
    ]
    last_error = None
    for fmt, headers in attempts:
        for retry in range(3):
            try:
                r = requests.get(url, headers=headers, timeout=60)
                if r.status_code == 404:          # series does not exist
                    return pd.Series(dtype="float64")
                r.raise_for_status()
                s = _parse_sdmx_json(r.json()) if fmt == "json" else _parse_sdmx_csv(r.text)
                return s[s.index >= pd.Timestamp(START_PERIOD)]
            except Exception as exc:  # network error or unexpected format
                last_error = exc
                time.sleep(1 + retry)
    raise RuntimeError(f"IMF download failed for {flow}/{key}: {last_error}")


def get_cpi(iso: str) -> pd.Series:
    return fetch_imf_series(CPI_FLOW, CPI_KEY.format(iso=iso))


def get_lcu_per_usd(iso: str) -> pd.Series:
    """Local-currency units per USD. The US dollar is 1 per USD by definition."""
    if iso == "USA":
        months = pd.date_range(START_PERIOD, pd.Timestamp.today(), freq="MS")
        return pd.Series(1.0, index=months)
    return fetch_imf_series(FX_FLOW, FX_KEY.format(iso=iso))


def build_table(iso1: str, iso2: str) -> pd.DataFrame:
    fx1, fx2 = get_lcu_per_usd(iso1), get_lcu_per_usd(iso2)
    p1, p2 = get_cpi(iso1), get_cpi(iso2)
    df = pd.concat(
        {"FX1_LCU_per_USD": fx1, "FX2_LCU_per_USD": fx2, "P1_CPI": p1, "P2_CPI": p2}, axis=1,
        sort=True,
    )
    df = df[df.index >= pd.Timestamp(START_PERIOD)]
    # Convert IMF quotes (LCU per USD) into S = Country 2 currency per 1 unit of Country 1 currency
    df["S"] = df["FX2_LCU_per_USD"] / df["FX1_LCU_per_USD"]
    df["RER"] = df["S"] * df["P1_CPI"] / df["P2_CPI"]
    df.index.name = "Month"
    return df


# ---------------------------------------------------------------------------
# User interface
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Real Exchange Rate App", layout="wide")
st.title("Real Exchange Rate App")
st.caption(
    "Monthly IMF data (CPI and period-average exchange rates) from January 1976 where available. "
    "S(t) = units of Country 2 currency per 1 unit of Country 1 currency; "
    "RER(t) = S(t) × P1(t) / P2(t)."
)

names = list(COUNTRIES.keys())
with st.sidebar:
    st.header("Countries")
    c1_name = st.selectbox("Country 1 (home)", names, index=names.index("United Kingdom"))
    c2_name = st.selectbox("Country 2 (foreign)", names, index=names.index("United States"))
iso1, iso2 = COUNTRIES[c1_name], COUNTRIES[c2_name]

if iso1 == iso2:
    st.warning("Please choose two different countries.")
    st.stop()

with st.spinner("Downloading IMF data..."):
    try:
        full = build_table(iso1, iso2)
    except Exception as exc:
        st.error(f"Could not retrieve IMF data. Error: {exc}")
        st.stop()

missing = [
    label
    for label, col in [
        (f"{c1_name} exchange rate", "FX1_LCU_per_USD"),
        (f"{c2_name} exchange rate", "FX2_LCU_per_USD"),
        (f"{c1_name} CPI", "P1_CPI"),
        (f"{c2_name} CPI", "P2_CPI"),
    ]
    if full[col].dropna().empty
]
if missing:
    st.error("The IMF returned no monthly data for: " + ", ".join(missing) + ".")
    st.stop()

valid_months = full.index[full["RER"].notna()]
if len(valid_months) == 0:
    st.error("No month has all four inputs (both exchange rates and both CPIs) available.")
    st.stop()

month_labels = [m.strftime("%Y-%m") for m in valid_months]
with st.sidebar:
    st.header("Sample period")
    start_label, end_label = st.select_slider(
        "Start and end month",
        options=month_labels,
        value=(month_labels[0], month_labels[-1]),
    )
    view = st.radio("Chart", ["Real", "Nominal", "Both"], index=2)

start, end = pd.Timestamp(start_label), pd.Timestamp(end_label)
sample = full.loc[start:end].copy()
sample["Valid"] = sample["RER"].notna()

rer_star = sample.loc[sample["Valid"], "RER"].mean()   # recalculated whenever dates change
sample["RER_star"] = rer_star
sample["Real_Index"] = 100 * sample["RER"] / rer_star

cur1 = f"{c1_name} currency"
cur2 = f"{c2_name} currency"
s_label = f"S: {cur2} per 1 unit of {cur1}"

# Summary metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Valid months", f"{int(sample['Valid'].sum())}")
m2.metric("RER* (sample average)", f"{rer_star:,.4f}")
m3.metric("Average Real Index", f"{sample.loc[sample['Valid'], 'Real_Index'].mean():.2f}")
m4.metric("Latest S", f"{sample['S'].dropna().iloc[-1]:,.4f}")
if sample["Valid"].sum() < len(sample):
    st.info(f"{len(sample) - int(sample['Valid'].sum())} month(s) in the sample have missing IMF inputs and are excluded from RER*.")

# Chart
plot = sample[sample["Valid"]]
real_trace = go.Scatter(x=plot.index, y=plot["Real_Index"], name="Real Index (avg = 100)", line=dict(color="#1f5fa8"))
nom_trace = go.Scatter(x=plot.index, y=plot["S"], name=f"Nominal S ({cur2} per {cur1})", line=dict(color="#d0742c"))

if view == "Both":
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(real_trace, secondary_y=False)
    fig.add_trace(nom_trace, secondary_y=True)
    fig.update_yaxes(title_text="Real Index (sample average = 100)", secondary_y=False)
    fig.update_yaxes(title_text=s_label, secondary_y=True)
else:
    fig = go.Figure(real_trace if view == "Real" else nom_trace)
    fig.update_yaxes(title_text="Real Index (sample average = 100)" if view == "Real" else s_label)
if view in ("Real", "Both"):
    fig.add_hline(y=100, line_dash="dot", line_color="gray")
fig.update_layout(
    title=f"{c1_name} vs {c2_name}: {start_label} to {end_label}",
    hovermode="x unified",
    legend=dict(orientation="h", y=-0.15),
    height=520,
)
st.plotly_chart(fig, width="stretch")
st.caption("A rise in the Real Index means Country 1 goods have become more expensive relative to Country 2 goods (a real appreciation of Country 1's currency).")

# Table and CSV download
export = sample.reset_index()
export["Month"] = export["Month"].dt.strftime("%Y-%m")
export.insert(1, "Country1", f"{c1_name} ({iso1})")
export.insert(2, "Country2", f"{c2_name} ({iso2})")
export = export[
    ["Month", "Country1", "Country2", "FX1_LCU_per_USD", "FX2_LCU_per_USD", "S",
     "P1_CPI", "P2_CPI", "RER", "RER_star", "Real_Index", "Valid"]
]

st.subheader("Data in the selected sample")
st.dataframe(export, width="stretch", hide_index=True)
st.download_button(
    "Download CSV",
    data=export.to_csv(index=False).encode("utf-8"),
    file_name=f"rer_{iso1}_{iso2}_{start_label}_{end_label}.csv",
    mime="text/csv",
)

with st.expander("Method and notes"):
    st.markdown(
        f"""
- **Source:** IMF SDMX 3.0 API (`{IMF_BASE}`), dataflows `CPI` (key `ISO3.CPI._T.IX.M`) and `ER` (key `ISO3.XDC_USD.PA_RT.M`).
- **Exchange rates:** the IMF reports local-currency units per USD. S(t) = (Country 2 LCU per USD) ÷ (Country 1 LCU per USD).
  The US dollar is set to 1 per USD.
- **RER(t)** = S(t) × P1(t) ÷ P2(t). **RER\\*** = mean of RER(t) over valid months between the chosen start and end months.
- **Real Index(t)** = 100 × RER(t) ÷ RER\\*. Nominal S(t) is shown in actual currency units (not normalized).
- Months where any of the four inputs is missing are excluded. IMF coverage differs by country (the Euro area, code G163, starts in 1999 for most series).
"""
    )
