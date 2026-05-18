# imports
import multiprocessing
from distributed import Client
import os
import json
import time
import copy
import numpy as np
from importlib.resources import files
import matplotlib.pyplot as plt
from ogeth.calibrate import Calibration
from ogcore.parameters import Specifications
from ogcore import output_tables as ot
from ogcore import output_plots as op
from ogcore.execute import runner
from ogcore.utils import safe_read_pickle
from ogeth.utils import is_connected
import ogcore.demographics as demog

# Use a custom matplotlib style file for plots
plt.style.use("ogcore.OGcorePlots")


def main():
    # Define parameters to use for multiprocessing
    num_workers = min(multiprocessing.cpu_count(), 7)
    client = Client(n_workers=num_workers, threads_per_worker=1)
    print("Number of workers = ", num_workers)

    # Directories to save data
    CUR_DIR = os.path.dirname(os.path.realpath(__file__))
    save_dir = os.path.join(CUR_DIR, "OG-ETH-Immigration")
    base_dir = os.path.join(save_dir, "OUTPUT_BASELINE")
    reform_dir = os.path.join(save_dir, "OUTPUT_REFORM")

    """
    ---------------------------------------------------------------------------
    Run baseline policy
    ---------------------------------------------------------------------------
    """
    # Set up baseline parameterization
    p = Specifications(
        baseline=True,
        num_workers=num_workers,
        baseline_dir=base_dir,
        output_base=base_dir,
    )
    # Update parameters for baseline from default json file
    with (
        files("ogeth")
        .joinpath("ogeth_default_parameters.json")
        .open("r") as file
    ):
        defaults = json.load(file)
    p.update_specifications(defaults)
    # Update parameters from calibrate.py Calibration class
    if is_connected():  # only update if connected to internet
        c = Calibration(
            p,
            update_from_api=True,
            demographic_data_path=os.path.join(CUR_DIR, "demographic_data"),
        )  # =True will update data from online sources
        updated_params = c.get_dict()
        p.update_specifications(updated_params)

    # Run model
    start_time = time.time()
    runner(p, time_path=True, client=client)
    print("run time = ", time.time() - start_time)

    """
    Run reform policy
    ---------------------------------------------------------------------------
    """

    # create new Specifications object for reform simulation
    p2 = copy.deepcopy(p)
    p2.baseline = False
    p2.output_base = reform_dir

    # Parameter change for the reform run
    # Find updated population objects
    # No read in each file and call get_pop_objs again with the data
    fert_rates = np.loadtxt(
        os.path.join(CUR_DIR, "demographic_data", "fert_rates.csv"),
        delimiter=",",
    )
    mort_rates = np.loadtxt(
        os.path.join(CUR_DIR, "demographic_data", "mort_rates.csv"),
        delimiter=",",
    )
    infmort_rates = np.loadtxt(
        os.path.join(CUR_DIR, "demographic_data", "infmort_rates.csv"),
        delimiter=",",
    )
    imm_rates = np.loadtxt(
        os.path.join(CUR_DIR, "demographic_data", "immigration_rates.csv"),
        delimiter=",",
    )
    pop_dist = np.loadtxt(
        os.path.join(
            CUR_DIR, "demographic_data", "population_distribution.csv"
        ),
        delimiter=",",
    )
    pre_pop_dist = np.loadtxt(
        os.path.join(
            CUR_DIR,
            "demographic_data",
            "pre_period_population_distribution.csv",
        ),
        delimiter=",",
    )

    # Extend fert_rates, mort_rates, infmort_rates, imm_rates to 50 periods
    fert_rates = np.append(
        fert_rates, np.tile(fert_rates[-1, :], (47, 1)), axis=0
    )
    mort_rates = np.append(
        mort_rates, np.tile(mort_rates[-1, :], (47, 1)), axis=0
    )

    infmort_rates = np.append(infmort_rates, np.tile(infmort_rates[-1], (47)))
    imm_rates = np.append(
        imm_rates, np.tile(imm_rates[-1, :], (47, 1)), axis=0
    )

    # Adjust immigration rates -- phase in and out a temporary
    # increase in immigration of 20-40 year olds
    adj_imm_rates = imm_rates
    adj_imm_rates[0, 20:40] += 0.0
    adj_imm_rates[1, 20:40] += 0.005
    adj_imm_rates[2, 20:40] += 0.01
    adj_imm_rates[3, 20:40] += 0.015
    adj_imm_rates[4:24, 20:40] += 0.02
    adj_imm_rates[24, 20:40] += 0.015
    adj_imm_rates[25, 20:40] += 0.01
    adj_imm_rates[26, 20:40] += 0.005

    print("Year diff = ", p2.start_year - p.start_year + 50)
    print("Shape fert_rates = ", fert_rates.shape)

    pop_dict2 = demog.get_pop_objs(
        p2.E,
        p2.S,
        p2.T,
        0,
        99,
        fert_rates=fert_rates,
        mort_rates=mort_rates,
        infmort_rates=infmort_rates,
        imm_rates=adj_imm_rates,
        infer_pop=True,
        pop_dist=pop_dist[0, :].reshape(1, p2.E + p2.S),
        pre_pop_dist=pre_pop_dist,
        initial_data_year=p2.start_year,
        final_data_year=p2.start_year + 49,
        GraphDiag=False,
    )
    p2.update_specifications(pop_dict2)
    p2.reform_use_baseline_solution = False

    # Run model
    start_time = time.time()
    runner(p2, time_path=True, client=client)
    print("run time = ", time.time() - start_time)
    client.close()

    """
    ---------------------------------------------------------------------------
    Save some results of simulations
    ---------------------------------------------------------------------------
    """
    base_tpi = safe_read_pickle(os.path.join(base_dir, "TPI", "TPI_vars.pkl"))
    base_params = safe_read_pickle(os.path.join(base_dir, "model_params.pkl"))
    reform_tpi = safe_read_pickle(
        os.path.join(reform_dir, "TPI", "TPI_vars.pkl")
    )
    reform_params = safe_read_pickle(
        os.path.join(reform_dir, "model_params.pkl")
    )
    ans = ot.macro_table(
        base_tpi,
        base_params,
        reform_tpi=reform_tpi,
        reform_params=reform_params,
        var_list=["Y", "C", "K", "L", "r", "w"],
        output_type="pct_diff",
        num_years=10,
        start_year=base_params.start_year,
    )

    # create plots of output
    op.plot_all(
        base_dir, reform_dir, os.path.join(save_dir, "OG-ETH_example_plots")
    )

    print("Percentage changes in aggregates:", ans)
    # save percentage change output to csv file
    ans.to_csv(os.path.join(save_dir, "OG-ETH_example_output.csv"))


if __name__ == "__main__":
    # execute only if run as a script
    main()
