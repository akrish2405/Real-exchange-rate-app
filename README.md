# Real Exchange Rate App

A Streamlit app that downloads monthly IMF data and computes the bilateral real exchange rate (RER) between any two IMF countries or the Euro area, from January 1976 where data exist.

**Live app:** _paste your streamlit.app link here_

## Economics

| Symbol | Definition |
|---|---|
| S(t) | Units of Country 2 currency per 1 unit of Country 1 currency |
| P1(t), P2(t) | Monthly CPI of Country 1 and Country 2 |
| RER(t) | S(t) × P1(t) / P2(t) |
| RER* | Average of RER(t) over valid months in the selected sample |
| Real Index(t) | 100 × RER(t) / RER* |

The IMF reports exchange rates as local-currency units (LCU) per USD, so the app converts them:

S(t) = (Country 2 LCU per USD) / (Country 1 LCU per USD)

The US dollar is set to 1 per USD. Example: with the UK as Country 1 and the US as Country 2, S = 1 / (GBP per USD) = **USD per GBP**.

A rise in the Real Index means Country 1 goods have become more expensive relative to Country 2 goods (a real appreciation of Country 1's currency).

## Features

- Choose Country 1 and Country 2 from IMF member countries and the Euro area (IMF code `G163`).
- Pick start and end months. RER* is recalculated whenever the dates change, so the Real Index averages 100 over the sample.
- Chart view: **Real** (index), **Nominal** (S in actual currency units, not normalized), or **Both** (two y-axes).
- CSV download of every month in the sample: both FX rates, S, both CPIs, RER, RER*, Real Index and a validity flag.

## Data

IMF SDMX 3.0 API: `https://api.imf.org/external/sdmx/3.0` (no API key needed)

- CPI (dataflow `IMF.STA/CPI`): `{ISO3}.CPI._T.IX.M`
- Exchange rate (dataflow `IMF.STA/ER`): `{ISO3}.XDC_USD.PA_RT.M` (period average, LCU per USD)

Months with any missing input are excluded from RER* and the charts. Coverage differs by country; the Euro area series start in 1999. Downloads are cached for 24 hours.

## Files

- `app.py`: the Streamlit app
- `requirements.txt`: Python packages
- `README.md`: this file

## Deploy

1. Put the three files at the top level of a public GitHub repository.
2. At [share.streamlit.io](https://share.streamlit.io), choose **Create app**, select the repository, branch `main` and file `app.py`.
3. In **Advanced settings**, choose Python 3.12, then **Deploy**.

## Credits

Code written with an LLM (_model name, date_). Prompts and economic checks by the author.
