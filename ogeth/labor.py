"""
------------------------------------------------------------------------
Computes the average labor participation rate for each age cohort.
------------------------------------------------------------------------
"""

import os
import numpy as np
import pandas as pd
import scipy.ndimage.filters as filter
from scipy import interpolate
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

CUR_DIR = os.path.abspath(os.path.dirname(__file__))


def get_labor_data(
    year=2023, data_dir=os.path.join(CUR_DIR, "..", "ogeth", "data", "qlfs")
):
    """
    Read in "raw" Quarterly Labour Force Survey data to calculate moments.

    Args:
        year (int): year of data to read in
        data_dir (str): path to directory with QLFS data

    Returns:
        df (Pandas DataFrame): QLFS data to compute labor supply from

    """
    # read in data for all quarters
    df_list = []
    for q in range(1, 5):
        file = os.path.join(data_dir, f"qlfs-{year}-q{q}-worker-v1.csv")
        df = pd.read_csv(file, encoding="latin-1", low_memory=False)
        df_list.append(df)
    df = pd.concat(df_list)

    # rename some variables
    df.rename(
        columns={
            "Q418HRSWRK": "hours",
            # "Q14AGE": "age",
            "age_grp1": "age_group",
            # "Hrswrk": "hours2",
            "Weight": "weight",
        },
        inplace=True,
    )
    # if hours is a string, take only part after space
    df["hours"] = df["hours"].str.split().str[-1]
    df["hours"] = pd.to_numeric(df["hours"], errors="coerce")
    # create weighted mean hours by age
    # replace missing hours with zero
    df["hours"] = df["hours"].fillna(0)
    # drop if hours are missing
    # df = df[~df['hours'].isna()]

    return df


def compute_labor_moments(df, S=80):
    """
    Compute moments from labor data.

    Args:
        df (Pandas DataFrame): QLFS data to compute labor supply from
        S (int): number of periods of economic life for model households

    Returns:
        labor_dist_out (Numpy array): fraction of time spent working
            by age

    """

    # Find fraction of total time people work on average by age group
    by_age = pd.DataFrame(
        df.groupby("age_group").apply(
            lambda x: (x["hours"] * x["weight"]).sum() / x["weight"].sum()
        )
    )
    # give column name to hours
    by_age.columns = ["hours"]
    # drop with indices that are in ['00-04', '05-09', '10-14', '14-Oct', '9-May']
    by_age = by_age.drop(["00-04", "05-09", "10-14", "14-Oct", "9-May"])
    # also drop age 15-19 since not in model
    # by_age = by_age.drop('15-19')
    # rename index for 75+ to 75-85 to be able to get midpoint
    by_age = by_age.rename(index={"75+": "75-85"})
    # compute midpoints of age groups
    age_midpoints = (
        pd.Series(by_age.index)
        .str.split("-")
        .apply(lambda x: (int(x[0]) + int(x[1])) / 2)
    )

    # get fraction of time endowment worked (assume time
    # endowment is 24 hours minus required time to sleep)
    by_age["frac_work"] = by_age["hours"] / ((24 - 8) * 7)

    # fit a cubic spline to these data points -- only through age 57
    # labor_dist = interpolate.interp1d(
    #     age_midpoints[:-5], by_age['frac_work'][:-5], kind='cubic')
    labor_dist = interpolate.interp1d(
        age_midpoints, by_age["frac_work"], kind="cubic"
    )
    # now evaluate the spline at each age
    labor_spline = labor_dist(np.linspace(20, 80, 60))

    # Data have sufficient obs through age  57 (55-59 age group)
    # Fit a line to the last few years of the average labor
    # participation which extends from ages 57 to 100.
    slope = (labor_spline[-1] - labor_spline[-8]) / (8 + 1)
    # intercept = by_age['frac_work'][-1] - slope*len(by_age['frac_work'])
    # extension = slope * (np.linspace(56, 80, 23)) + intercept
    # to_dot = slope * (np.linspace(45, 56, 11)) + intercept

    labor_dist_data = np.zeros(80)
    labor_dist_data[:60] = labor_spline
    labor_dist_data[60:] = labor_spline[-1] + slope * range(20)

    # the above computes moments if the model period is a year
    # the following adjusts those moments in case it is smaller
    labor_dist_out = (
        1  # filter.uniform_filter(labor_dist_data, size=int(80 / S))[
    )
    #     :: int(80 / S)
    # ]

    return labor_dist_data, age_midpoints, by_age, labor_dist_out


def VCV_moments(qlfs, n=1000, S=80):
    """
    Compute Variance-Covariance matrix for labor moments by
    bootstrapping data.

    Args:
        cps (Pandas DataFrame): CPS data to compute labor supply from
        S (int): number of periods of economic life for model households
        n (int): number of bootstrap iterations to run
        bin_weights (Numpy array): ability weight, length J

    Output:
        VCV (Numpy array): = variance-covariance matrix of labor
            moments, size SxS

    """
    labor_moments_boot = np.zeros((n, S))
    for i in range(n):
        boot = qlfs[np.random.randint(2, size=len(qlfs.index)).astype(bool)]
        _, _, _, labor_moments_boot[i, :] = compute_labor_moments(boot, S)

    VCV = np.cov(labor_moments_boot.T)

    return VCV


def labor_data_graphs(
    year=2023,
    data_dir=os.path.join(CUR_DIR, "..", "ogeth", "data", "qlfs"),
    S=80,
    output_dir=None,
):
    """
    Plot labor supply data.

    Args:
        weighted (Numpy array):
        S (int): number of periods of economic life for model households
        J (int): number of lifetime income groups
        output_dir (str): path to save figures to

    Returns:
        None

    """
    # get labor data
    interpolated_data, age_midpoints, by_age, _ = compute_labor_moments(
        get_labor_data(year, data_dir), S
    )
    plt.plot(np.linspace(20, 100, 80), interpolated_data)
    # add scatter plot of raw data
    plt.scatter(age_midpoints, by_age["frac_work"], color="red", alpha=0.5)
    plt.xlabel("Age")
    plt.ylabel("Labor supply")
    plt.title("Labor supply by age")
    plt.legend(["Interpolated", "Data"])
    if output_dir:
        plt.savefig(
            os.path.join(output_dir, "labor_dist_data.png"),
            bbox_inches="tight",
            dpi=300,
        )
    else:
        return plt
