import multiprocessing
from multiprocessing import freeze_support
from distributed import Client
import os
import json
from importlib.resources import files
from ogeth import estimate_chi_n as est
from ogcore.parameters import Specifications


def main():
    # Define parameters to use for multiprocessing
    num_workers = min(multiprocessing.cpu_count(), 7)
    client = Client(n_workers=num_workers, threads_per_worker=1)
    print("Number of workers = ", num_workers)

    # Directories to save data
    CUR_DIR = os.path.dirname(os.path.realpath(__file__))
    save_dir = os.path.join(CUR_DIR, "OG-ETH-Example")
    base_dir = os.path.join(save_dir, "OUTPUT_BASELINE")

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

    # Estimate chi_n
    chi_params = est.chi_estimate(p, client, estimate=False, plot=True)
    print("Estimated chi_n = ", chi_params)
    client.close()


if __name__ == "__main__":
    freeze_support()
    main()
