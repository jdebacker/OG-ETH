"""
This module uses data from World Bank WDI, World Bank Quarterly Public
Sector Debt (QPSD) database, the IMF, and UN ILO to find values for
parameters for the OG-ETH model that rely on macro data for calibration.
"""

# imports
import pandas as pd
import numpy as np
import requests
import datetime
from io import StringIO
from pathlib import Path

# Public capital elasticity; see firms.md.
GAMMA_G_LIC = 0.1

# Start year for the g_y_annual average-growth calculation; matches the
# documented window in macro.md (average annual GDP-per-capita growth
# 2006-2024 = 6.0%).
G_Y_START_YEAR = 2006


def _fetch_wb_data(indicators, country_iso, start_year, end_year, source):
    """
    Fetch a set of World Bank indicators and return a single DataFrame.

    Args:
        indicators (dict): mapping of human-readable labels to indicator codes
        country_iso (str): ISO country code
        start_year (int): first year to request
        end_year (int): last year to request
        source (int): World Bank source ID

    Returns:
        pandas.DataFrame: DataFrame indexed by year/quarter label
    """
    if source == 2:
        date_range = f"{start_year}:{end_year}"
    elif source == 20:
        date_range = f"{start_year}Q1:{end_year}Q4"
    else:
        raise ValueError(f"Unsupported World Bank source: {source}")

    data_frames = []
    for label, indicator_code in indicators.items():
        response = requests.get(
            (
                "https://api.worldbank.org/v2/country/"
                f"{country_iso}/indicator/{indicator_code}"
            ),
            params={
                "date": date_range,
                "source": source,
                "format": "json",
                "per_page": 10000,
            },
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError(
                f"Malformed World Bank response for {indicator_code}"
            ) from exc

        if (
            not isinstance(payload, list)
            or len(payload) < 2
            or not isinstance(payload[1], list)
            or not payload[1]
        ):
            raise ValueError(
                f"Empty or malformed World Bank response for {indicator_code}"
            )

        series_data = {}
        for row in payload[1]:
            date = row.get("date")
            if date is None:
                continue
            series_data[date] = row.get("value")

        if not series_data:
            raise ValueError(
                "No dated observations in World Bank response "
                f"for {indicator_code}"
            )

        series = pd.Series(series_data, name=label)
        series = pd.to_numeric(series, errors="coerce")
        data_frames.append(series.to_frame())

    data = pd.concat(data_frames, axis=1)
    data.index.name = "year"
    # Preserve descending time order used by the existing pct_change(-1) logic.
    data = data.sort_index(ascending=False)
    return data


def _get_imf_macro_params(
    country_iso,
    target_year,
    data_path=None,
):
    """
    Fetch IMF GFS data and compute alpha_T and alpha_G.

    Args:
        country_iso (str): ISO alpha-3 country code
        target_year (int): preferred calibration year
        data_path (str | Path | None): optional path to save IMF CSV data

    Returns:
        dict: IMF-derived macro parameters
    """
    required_indicators = {"G2_T", "G24_T", "G27_T", "G271_T"}
    data_path = Path(data_path) if data_path is not None else None
    response = requests.get(
        (
            "https://api.imf.org/external/sdmx/3.0/data/dataflow/"
            f"IMF.STA/GFS_SOO/12.0.0/"
            f"{country_iso}.S1311.G2M.*.POGDP_PT.A"
        ),
        timeout=30,
    )
    response.raise_for_status()
    try:
        payload = response.json()
        data = payload["data"]
        structure = data["structures"][0]
        data_set = data["dataSets"][0]
        series_dimensions = structure["dimensions"]["series"]
        observation_years = [
            value.get("id", value.get("value"))
            for value in structure["dimensions"]["observation"][0]["values"]
        ]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise ValueError(
            "Empty or malformed IMF response for GFS_SOO"
        ) from exc

    records = []
    for series_key, series in data_set["series"].items():
        dimension_indexes = [int(idx) for idx in series_key.split(":")]
        labels = {
            dim["id"]: dim["values"][idx]["id"]
            for dim, idx in zip(series_dimensions, dimension_indexes)
        }
        indicator = labels.get("INDICATOR")
        if indicator not in required_indicators:
            continue
        for observation_key, observation in series.get(
            "observations", {}
        ).items():
            value = observation[0]
            if value is None:
                continue
            records.append(
                {
                    "year": observation_years[int(observation_key)],
                    "indicator": indicator,
                    "value": float(value),
                    "country_iso": country_iso,
                    "sector": "S1311",
                    "dataset": "IMF.STA:GFS_SOO(12.0.0)",
                }
            )

    imf_data = pd.DataFrame(records)
    if imf_data.empty:
        raise ValueError("Empty or malformed IMF response for GFS_SOO")

    if data_path is not None:
        data_path.parent.mkdir(parents=True, exist_ok=True)
        imf_data.sort_values(["indicator", "year"]).to_csv(
            data_path, index=False
        )
        print(f"IMF data saved to {data_path}")

    imf_data["year"] = pd.to_numeric(imf_data["year"], errors="coerce")
    imf_data["value"] = pd.to_numeric(imf_data["value"], errors="coerce")
    imf_data = imf_data.dropna(subset=["year", "value"])

    available = (
        imf_data.pivot_table(
            index="year", columns="indicator", values="value", aggfunc="first"
        )
        .sort_index()
        .dropna(subset=sorted(required_indicators))
    )
    available = available.loc[available.index <= int(target_year)]

    if available.empty:
        raise ValueError(
            f"No complete IMF data available for {country_iso} "
            f"up to {target_year}"
        )

    selected_year = (
        int(target_year)
        if int(target_year) in available.index
        else int(available.index.max())
    )
    if selected_year != int(target_year):
        print(
            f"Warning: No IMF data for {target_year}. "
            f"Using last available year: {selected_year}"
        )

    values = available.loc[selected_year]
    return {
        "alpha_T": [(values["G27_T"] - values["G271_T"]) / 100],
        "alpha_G": [
            (values["G2_T"] - values["G24_T"] - values["G27_T"]) / 100
        ],
    }


def get_macro_params(
    data_start_date=datetime.datetime(1947, 1, 1),
    data_end_date=datetime.datetime(2024, 12, 31),
    country_iso="ETH",
    update_from_api=False,
    imf_data_year=None,
    imf_data_path=None,
):
    """
    Compute values of parameters that are derived from macro data

    Args:
        data_start_date (datetime): start date for data
        data_end_date (datetime): end date for data
        country_iso (str): ISO code for country
        imf_data_year (int | None): IMF target year override. Defaults to
            data_end_date.year when None.
        imf_data_path (str | Path | None): optional path to save IMF CSV data

    Returns:
        macro_parameters (dict): dictionary of parameter values
    """
    # initialize a dictionary of parameters
    macro_parameters = {}

    """
    Retrieve data from the World Bank World Development Indicators.
    """
    # Dictionaries of variables and their corresponding World Bank codes
    # Annual data
    wb_a_variable_dict = {
        "GDP per capita (constant 2015 US$)": "NY.GDP.PCAP.KD",
        "Real GDP (constant 2015 US$)": "NY.GDP.MKTP.KD",
        "Nominal GDP (current US$)": "NY.GDP.MKTP.CD",
        (
            "General government final consumption expenditure (current US$)"
        ): "NE.CON.GOVT.CD",
    }
    # Quarterly public-sector-debt (QPSD) indicators are intentionally
    # not fetched for OG-ETH: the World Bank QPSD database has no Ethiopia
    # data. The debt parameters (initial_debt_ratio,
    # initial_foreign_debt_ratio, zeta_D) are hand-calibrated from the
    # Ethiopia MoF Public Sector Debt Bulletin No. 51 (see macro.md).
    if update_from_api:
        try:
            wb_data_a = _fetch_wb_data(
                wb_a_variable_dict,
                country_iso,
                data_start_date.year,
                data_end_date.year,
                source=2,
            )
            # Compute annual GDP-per-capita growth (g_y_annual) from the
            # World Bank WDI series, averaging pct_change from
            # G_Y_START_YEAR onward to match the documented window (see
            # macro.md). Debt parameters are not derived here (see note
            # above).
            if "GDP per capita (constant 2015 US$)" in wb_data_a.columns:
                gdp_pc = wb_data_a["GDP per capita (constant 2015 US$)"]
                gdp_pc = gdp_pc[gdp_pc.index.astype(int) >= G_Y_START_YEAR]
                g_y_series = gdp_pc.pct_change(-1)

                # If all values are NaN, return None
                macro_parameters["g_y_annual"] = (
                    g_y_series.mean() if not g_y_series.isna().all() else None
                )
                print(
                    "g_y_annual updated from World Bank API: "
                    f"{macro_parameters['g_y_annual']}"
                )
            else:
                print(
                    "Warning: Missing GDP per capita data in World "
                    "Bank data. Skipping update for g_y_annual."
                )
        except Exception:
            print("Failed to retrieve data from World Bank")
            print("Will not update g_y_annual")
    else:
        print("Not updating from World Bank API")

    """
    Retrieve labour share data from the United Nations ILOSTAT Data API
    (see https://rshiny.ilo.org/dataexplorer9/?lang=en).
    The series code is SDG_1041_NOC_RT_A (labour income share as a percent
    of GDP). Total capital share equals 1 - labour share. We subtract
    GAMMA_G_LIC, which matches the gamma_g value in
    'default_parameters.json', to recover the private capital share gamma.
    If this fails we will not update gamma in 'default_parameters.json'.
    """
    if update_from_api:
        try:
            target = (
                "https://rplumber.ilo.org/data/indicator/"
                + "?id=SDG_1041_NOC_RT_A"
                + "&ref_area="
                + str(country_iso)
                + "&timefrom="
                + str(data_start_date.year)
                + "&timeto="
                + str(data_end_date.year)
                + "&type=both&format=.csv"
            )
            # Add headers
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }

            print("Attempting to update gamma from ILOSTAT")
            response = requests.get(target, headers=headers)
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
            else:
                print("Request successful.")
            csv_content = StringIO(response.text)
            df_temp = pd.read_csv(csv_content)
            ilo_data = df_temp[["time", "obs_value"]]
            # find gamma (private capital share) by subtracting GAMMA_G_LIC
            # from the ILOSTAT-derived total capital share.
            labor_share = (
                ilo_data.loc[
                    ilo_data["time"] == data_end_date.year, "obs_value"
                ].squeeze()
                / 100
            )
            macro_parameters["gamma"] = [1 - labor_share - GAMMA_G_LIC]
            print(
                f"gamma updated from ILOSTAT API: {macro_parameters['gamma']}"
            )
        except Exception:
            print("Failed to retrieve data from ILOSTAT")
            print("Will not update gamma")
    else:
        print("Not updating from ILOSTAT API")

    """
    Estimate r_gov_shift and r_gov_scale (Li, Magud, Werner 2021 method).
    """

    # alpha_T and alpha_G are NOT pulled from the IMF API for OG-ETH: the
    # IMF SDMX endpoint returns only 2002-vintage data for Ethiopia, and
    # the documented sources differ (alpha_G -> World Bank NE.CON.GOVT.ZS;
    # alpha_T -> IMF GFS + IMF Country Report 25/188, hand-combined). Both
    # stay at the committed values in macro.md. _get_imf_macro_params is
    # retained (tested independently) for reuse if wired to the right data.
    if update_from_api:
        """"
        Estimate the discount on sovereign yields relative to private debt
        Follow the methodology in Li, Magud, Werner, Witte (2021)
        available at:
        https://www.imf.org/en/Publications/WP/Issues/2021/06/04/The-Long-Run-Impact-of-Sovereign-Yields-on-Corporate-Yields-in-Emerging-Markets-50224
        discussion is here: https://github.com/EAPD-DRB/OG-ZAF/issues/22
        Steps:
        1) Generate modelled corporate yields (corp_yhat) for a range of
        sovereign yields (sov_y)  using the estimated equation in col 2 of
        table 8 (and figure 3). 2) Estimate the OLS using sovereign yields
        as the dependent variable
        """
        try:
            import statsmodels.api as sm

            # # estimate r_gov_shift and r_gov_scale
            sov_y = np.arange(20, 120) / 10
            corp_yhat = 8.199 - (2.975 * sov_y) + (0.478 * sov_y**2)
            corp_yhat = sm.add_constant(corp_yhat)
            mod = sm.OLS(
                sov_y,
                corp_yhat,
            )
            res = mod.fit()
            # First term is the constant and needs to be divided by 100 to have
            # the correct unit. Second term is the coefficient
            macro_parameters["r_gov_shift"] = [-res.params[0] / 100]
            macro_parameters["r_gov_scale"] = [res.params[1]]
            print(
                "r_gov_shift computed (LMW 2021 method): "
                f"{macro_parameters['r_gov_shift']}"
            )
            print(
                "r_gov_scale computed (LMW 2021 method): "
                f"{macro_parameters['r_gov_scale']}"
            )
        except Exception:
            print("Failed to compute r_gov_shift, r_gov_scale")
            print("Will not update r_gov_shift, r_gov_scale")
    else:
        print("Not computing r_gov_shift, r_gov_scale")

    return macro_parameters
