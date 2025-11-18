"""
This module uses data from World Bank WDI, World Bank Quarterly Public
Sector Debt (QPSD) database, the IMF, and UN ILO to find values for
parameters for the OG-ETH model that rely on macro data for calibration.
"""

# imports
from pandas_datareader import wb
import pandas as pd
import numpy as np
import requests
import datetime
import statsmodels.api as sm
from io import StringIO


def get_macro_params(
    data_start_date=datetime.datetime(1947, 1, 1),
    data_end_date=datetime.datetime(2024, 12, 31),
    country_iso="ETH",
    update_from_api=False,
):
    """
    Compute values of parameters that are derived from macro data

    Args:
        data_start_date (datetime): start date for data
        data_end_date (datetime): end date for data
        country_iso (str): ISO code for country

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
        # "Real GDP (constant 2015 US$)": "NY.GDP.MKTP.KD",
        # "Nominal GDP (current US$)": "NY.GDP.MKTP.CD",
        # "General government final consumption expenditure (current US$)": "NE.CON.GOVT.CD",
    }

    if update_from_api:
        try:
            # pull series of interest from the WB using pandas_datareader
            # Annual data
            wb_data_a = wb.download(
                indicator=wb_a_variable_dict.values(),
                country=country_iso,
                start=data_start_date,
                end=data_end_date,
            )
            wb_data_a.rename(
                columns=dict((y, x) for x, y in wb_a_variable_dict.items()),
                inplace=True,
            )

            # Compute annual GDP growth safely
            if "GDP per capita (constant 2015 US$)" in wb_data_a.columns:
                g_y_series = wb_data_a[
                    "GDP per capita (constant 2015 US$)"
                ].pct_change(-1)

                # If all values are NaN, return None
                macro_parameters["g_y_annual"] = (
                    g_y_series.mean() if not g_y_series.isna().all() else None
                )
            else:
                print(
                    "Warning: Missing GDP per capita data in World Bank data. Skipping update for g_y_annual."
                )

            print(
                f"g_y_annual updated from World Bank API: {macro_parameters['g_y_annual']}"
            )
        except:
            print("Failed to retrieve data from World Bank")
            print("Will not update the following parameters:")
            print(
                "[initial_debt_ratio, initial_foreign_debt_ratio, zeta_D, g_y]"
            )
    else:
        print("Not updating from World Bank API")

    """
    Retrieve labour share data from the United Nations ILOSTAT Data API
    (see https://rplumber-test.ilo.org)
    The series code is SDG_1041_NOC_RT_A (capital share)
    Labor share (gamma) = 1 - capital share
    If this fails we will not update gamma in 'default_parameters.json'
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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
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
            # find gamma, capital's share of income
            macro_parameters["gamma"] = [
                1
                - (
                    (
                        ilo_data.loc[
                            ilo_data["time"] == data_end_date.year, "obs_value"
                        ].squeeze()
                    )
                    / 100
                )
            ]
            print(
                f"gamma updated from ILOSTAT API: {macro_parameters['gamma']}"
            )
        except:
            print("Failed to retrieve data from ILOSTAT")
            print("Will not update gamma")
    else:
        print("Not updating from ILOSTAT API")

    """
    Calibrate parameters from IMF and other sources
    """

    if update_from_api:
        # alpha_T, non-social security transfers (grants, subsidies, and other transfers) as a fraction of GDP
        # source: IMF GFS (12.0.0), indicator G271_T, Budgetary central government
        # source link: https://data.imf.org/en/Data-Explorer?datasetUrn=IMF.STA:GFS_SOO(12.0.0)&INDICATOR=G271_T
        # 2023 = 3.38% of GDP
        macro_parameters["alpha_T"] = [0.034 + 0.016]  # including social benefits of 1.6% of GDP

        # alpha_G, total government expenditure as a fraction of GDP
        # source: IMF WEO (9.0.0), indicator GGX, General government expenditure (% of GDP)
        # source link: https://data.imf.org/en/Data-Explorer?datasetUrn=IMF.RES:WEO(9.0.0)&INDICATOR=GGX
        # 2024 = 9.538% of GDP
        macro_parameters["alpha_G"] = [0.095]

        # initial_debt_ratio, gross general government debt as a fraction of GDP
        # source: from the IMF WEO, Series ETH.GGXWDG_NGDP.A — Gross general government debt (% of GDP).
        # The IMF value annualizes Ethiopia’s fiscal year data (July–June) to the calendar year.
        # 2023/24 (mapped to CY2024) = 32.66% of GDP
        macro_parameters["initial_debt_ratio"] = 0.327

        # initial_foreign_debt_ratio, share of external debt in total public sector debt
        # source: Ministry of Finance, Public Sector Debt Portfolio Analysis No. 25 (2019/20–2023/24)
        # source link: https://www.mofed.gov.et/resources/bulletin/
        # FY2023/24: external debt USD 28.89 billion; total public debt USD 68.86 billion → 42%
        macro_parameters["initial_foreign_debt_ratio"] = 0.42

        # zeta_D, share of new government debt issues purchased by foreign creditors
        # source: Ministry of Finance, Public Sector Debt Portfolio Analysis No. 25 (2019/20–2023/24), Table 1
        # source link: https://www.mofed.gov.et/resources/bulletin/
        # FY2023/24: Δ total debt = +5.53 bn; Δ external debt = +0.64 bn → external share ≈ 11.6%
        # Caution: there is significant annual variatiot: 2020/21 = 49.9, 2021/22 = –152.5, 2022/23 = 5.0, 2023/24 = 11.6
        # We use the latest year.
        macro_parameters["zeta_D"] = [0.12]

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
        # Report new values
        print(f"alpha_T updated from IMF data: {macro_parameters['alpha_T']}")
        print(f"alpha_G updated from IMF data: {macro_parameters['alpha_G']}")
        print(
            f"r_gov_shift updated from IMF data: {macro_parameters['r_gov_shift']}"
        )
        print(
            f"r_gov_scale updated from IMF data: {macro_parameters['r_gov_scale']}"
        )
    else:
        print("Not updating alpha_T, alpha_G, r_gov_shift, r_gov_scale")

    return macro_parameters
