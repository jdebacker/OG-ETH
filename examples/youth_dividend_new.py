# imports
import numpy as np
import multiprocessing
from distributed import Client
import os
import json
import time
import copy
from importlib.resources import files
import matplotlib.pyplot as plt
from ogeth.calibrate import Calibration
from ogcore.parameters import Specifications
from ogcore import output_tables as ot
from ogcore import output_plots as op
from ogcore.execute import runner
from ogcore.utils import safe_read_pickle
from ogeth.utils import is_connected
import dask
dask.config.set(scheduler="synchronous")

# Use a custom matplotlib style file for plots
plt.style.use("ogcore.OGcorePlots")


def main():
    # Define parameters to use for multiprocessing
    num_workers = min(multiprocessing.cpu_count(), 2)
    client = Client(n_workers=num_workers, threads_per_worker=1)
    print("Number of workers = ", num_workers)

    # Directories to save data
    CUR_DIR = os.path.dirname(os.path.realpath(__file__))
    save_dir = os.path.join(CUR_DIR, "YouthDividend")
    base_dir = os.path.join(save_dir, "OUTPUT_BASELINE")

    # Reform directories — one per scenario
    d2_dir = os.path.join(save_dir, "OUTPUT_D2_FERTILITY_DECLINE")
    d3_dir = os.path.join(save_dir, "OUTPUT_D3_MORTALITY_SHOCK")
    d4_dir = os.path.join(save_dir, "OUTPUT_D4_HIGH_FERTILITY")

    e2_dir = os.path.join(save_dir, "OUTPUT_E2_TVET_MODERATE")
    e3_dir = os.path.join(save_dir, "OUTPUT_E3_UNIVERSITY_STRONG")
    e4_dir = os.path.join(save_dir, "OUTPUT_E4_COMBINED_MAX")

    l2_dir = os.path.join(save_dir, "OUTPUT_L2_FORMALISATION_25")
    l3_dir = os.path.join(save_dir, "OUTPUT_L3_FORMALISATION_40")
    l4_dir = os.path.join(save_dir, "OUTPUT_L4_FORMALISATION_55")

    g2_dir = os.path.join(save_dir, "OUTPUT_G2_FLFP_PARTIAL")
    g3_dir = os.path.join(save_dir, "OUTPUT_G3_FLFP_FULL_2040")
    g4_dir = os.path.join(save_dir, "OUTPUT_G4_FLFP_FULL_2030")

    m2_dir = os.path.join(save_dir, "OUTPUT_M2_BRAIN_DRAIN_MOD")
    m3_dir = os.path.join(save_dir, "OUTPUT_M3_BRAIN_DRAIN_SEV")
    m4_dir = os.path.join(save_dir, "OUTPUT_M4_BRAIN_GAIN")

    f2_dir = os.path.join(save_dir, "OUTPUT_F2_EDU_SURGE")
    f3_dir = os.path.join(save_dir, "OUTPUT_F3_EMPLOY_SUBSIDY")
    f4_dir = os.path.join(save_dir, "OUTPUT_F4_GENDER_INVESTMENT")
    f5_dir = os.path.join(save_dir, "OUTPUT_F5_IMF_CONSTRAINT")

    i1_dir = os.path.join(save_dir, "OUTPUT_I1_MODERATE")
    i2_dir = os.path.join(save_dir, "OUTPUT_I2_AMBITIOUS")
    i3_dir = os.path.join(save_dir, "OUTPUT_I3_MAXIMUM")
    i4_dir = os.path.join(save_dir, "OUTPUT_I4_DELAYED_ACTION")

    """
    ---------------------------------------------------------------------------
    Run baseline policy (D1)
    UN WPP 2024 medium-fertility, current fiscal policy
    ---------------------------------------------------------------------------
    """
    p = Specifications(
        baseline=True,
        num_workers=num_workers,
        baseline_dir=base_dir,
        output_base=base_dir,
    )
    with (
        files("ogeth")
        .joinpath("ogeth_default_parameters.json")
        .open("r") as file
    ):
        defaults = json.load(file)
    p.update_specifications(defaults)
    if is_connected():
        c = Calibration(p, update_from_api=False)
        p.update_specifications(c.get_dict())

    start_time = time.time()
    runner(p, time_path=True, client=client)
    print("Baseline run time = ", time.time() - start_time)

    """
    ---------------------------------------------------------------------------
    DIMENSION 1 — Demographic Foundation
    ---------------------------------------------------------------------------
    """

    ##### D2 — Accelerated Fertility Decline
    # TFR reaches 2.5 by 2035 rather than 2045
    # Modelled as 30% faster decline in population growth over 2025-2035
    # [Source: UN WPP 2024 low-fertility variant; ILO 2023]
    p_d2 = copy.deepcopy(p)
    p_d2.baseline = False
    p_d2.output_base = d2_dir

    # g_n_ss is the dominant eigenvalue of the full demographic transition matrix
    # (fertility × mortality × immigration) and cannot be changed consistently
    # without a full demographic recalibration.  Model the accelerated fertility
    # decline as a transition-path shock only: g_n[t] is lower through the TPI
    # horizon and then tapers back to g_n_ss so the SS remains well-posed.
    g_n_d2 = np.array(p.g_n, dtype=float)
    g_n_d2[:10] *= np.linspace(1.0, 0.75, 10)
    g_n_d2[10:p.T] *= 0.75
    taper_d2 = np.linspace(g_n_d2[p.T - 1], float(p.g_n_ss), p.S + 1)[1:]
    g_n_d2[p.T:] = taper_d2

    p_d2.update_specifications({"g_n": g_n_d2.tolist()})

    start_time = time.time()
    runner(p_d2, time_path=True, client=client)
    print("D2 run time = ", time.time() - start_time)

    ##### D3 — High Youth Mortality Shock
    # Conflict or health crisis raises youth mortality by 15%
    # Affects model age periods 0-15 (ages 20-35) for first 20 periods
    # [Source: World Bank Ethiopia Conflict Impact Report 2023]
    p_d3 = copy.deepcopy(p)
    p_d3.baseline = False
    p_d3.output_base = d3_dir

    rho_d3 = np.array(p.rho, dtype=float)
    rho_d3[:20, :15] *= 1.15
    rho_d3 = np.clip(rho_d3, 0.0, 0.999)
    p_d3.rho = rho_d3  # direct override — bypasses paramtools

    start_time = time.time()
    runner(p_d3, time_path=True, client=client)
    print("D3 run time = ", time.time() - start_time)

    ##### D4 — High Fertility Upper Bound
    # Population exceeds 200M by 2050 — UN high-fertility variant
    # 30% higher population growth through 2035, slower decline thereafter
    # [Source: UN WPP 2024 high-fertility variant]
    p_d4 = copy.deepcopy(p)
    p_d4.baseline = False
    p_d4.output_base = d4_dir

    # Same reasoning as D2: only modify the transition path, not g_n_ss.
    g_n_d4 = np.array(p.g_n, dtype=float)
    g_n_d4[:26] *= 1.30
    g_n_d4[26:p.T] *= 1.15
    taper_d4 = np.linspace(g_n_d4[p.T - 1], float(p.g_n_ss), p.S + 1)[1:]
    g_n_d4[p.T:] = taper_d4

    p_d4.update_specifications({"g_n": g_n_d4.tolist()})

    start_time = time.time()
    runner(p_d4, time_path=True, client=client)
    print("D4 run time = ", time.time() - start_time)

    """
    ---------------------------------------------------------------------------
    DIMENSION 2 — Education and Human Capital
    ---------------------------------------------------------------------------
    """

    ##### E2 — Moderate TVET Expansion
    # Age-efficiency units of young workers (ages 20-35) raised by 10%
    # tapering to 0 by age 55. Represents improved vocational training.
    # [Source: World Bank Ethiopia Education Report 2023; ILO 2023]
    p_e2 = copy.deepcopy(p)
    p_e2.baseline = False
    p_e2.output_base = e2_dir

    e0_e2 = np.array(p.e, dtype=float)
    e0_e2 = e0_e2[0] if e0_e2.ndim == 3 else e0_e2  # (S, J)
    ages_e2 = np.linspace(p.starting_age, p.starting_age + p.S, p.S, endpoint=False)
    factor_e2 = np.zeros(p.S)
    for i, a in enumerate(ages_e2):
        if a <= 35:
            factor_e2[i] = 0.10
        elif a < 55:
            factor_e2[i] = 0.10 * (55 - a) / (55 - 35)
    e_new_e2 = e0_e2 * (1.0 + factor_e2[:, np.newaxis])

    p_e2.update_specifications({"e": e_new_e2.tolist()})

    start_time = time.time()
    runner(p_e2, time_path=True, client=client)
    print("E2 run time = ", time.time() - start_time)

    ##### E3 — Strong University Quality Improvement
    # Age-efficiency units raised by 20% — stronger reform
    # [Source: World Bank Ethiopia Education Report 2023]
    p_e3 = copy.deepcopy(p)
    p_e3.baseline = False
    p_e3.output_base = e3_dir

    e0_e3 = np.array(p.e, dtype=float)
    e0_e3 = e0_e3[0] if e0_e3.ndim == 3 else e0_e3
    ages_e3 = np.linspace(p.starting_age, p.starting_age + p.S, p.S, endpoint=False)
    factor_e3 = np.zeros(p.S)
    for i, a in enumerate(ages_e3):
        if a <= 35:
            factor_e3[i] = 0.20
        elif a < 55:
            factor_e3[i] = 0.20 * (55 - a) / (55 - 35)
    e_new_e3 = e0_e3 * (1.0 + factor_e3[:, np.newaxis])

    p_e3.update_specifications({"e": e_new_e3.tolist()})

    start_time = time.time()
    runner(p_e3, time_path=True, client=client)
    print("E3 run time = ", time.time() - start_time)

    ##### E4 — Combined TVET + University Reform (Maximum Human Capital)
    # Age-efficiency units raised by 25% — full combined reform
    # [Source: World Bank Ethiopia Education Report 2023; ILO 2023]
    p_e4 = copy.deepcopy(p)
    p_e4.baseline = False
    p_e4.output_base = e4_dir

    e0_e4 = np.array(p.e, dtype=float)
    e0_e4 = e0_e4[0] if e0_e4.ndim == 3 else e0_e4
    ages_e4 = np.linspace(p.starting_age, p.starting_age + p.S, p.S, endpoint=False)
    factor_e4 = np.zeros(p.S)
    for i, a in enumerate(ages_e4):
        if a <= 35:
            factor_e4[i] = 0.25
        elif a < 55:
            factor_e4[i] = 0.25 * (55 - a) / (55 - 35)
    e_new_e4 = e0_e4 * (1.0 + factor_e4[:, np.newaxis])

    p_e4.update_specifications({"e": e_new_e4.tolist()})

    start_time = time.time()
    runner(p_e4, time_path=True, client=client)
    print("E4 run time = ", time.time() - start_time)

    """
    ---------------------------------------------------------------------------
    DIMENSION 3 — Labour Market and Formalisation
    Productivity premium derivation (ILO 2023):
      Formal workers earn 2.5x informal workers in Ethiopia
      Baseline: 0.13*2.5 + 0.87*1.0 = 1.195
      L2 (25%): 0.25*2.5 + 0.75*1.0 = 1.375 -> boost = +15.1%
      L3 (40%): 0.40*2.5 + 0.60*1.0 = 1.600 -> boost = +33.9%
      L4 (55%): 0.55*2.5 + 0.45*1.0 = 1.825 -> boost = +52.7%
    ---------------------------------------------------------------------------
    """

    ##### L2 — Moderate Formalisation (13% -> 25% formal share by 2035)
    # e +15.1% for working-age workers; frisch +0.05 (reduced frictions)
    # [Source: ILO Ethiopia Labour Market Profile 2023]
    p_l2 = copy.deepcopy(p)
    p_l2.baseline = False
    p_l2.output_base = l2_dir

    e0_l2 = np.array(p.e, dtype=float)
    e0_l2 = e0_l2[0] if e0_l2.ndim == 3 else e0_l2
    ages_l2 = np.linspace(p.starting_age, p.starting_age + p.S, p.S, endpoint=False)
    factor_l2 = np.zeros(p.S)
    for i, a in enumerate(ages_l2):
        if 20 <= a <= 55:
            factor_l2[i] = 0.151
        elif 55 < a < 65:
            factor_l2[i] = 0.151 * (65 - a) / (65 - 55)
    e_new_l2 = e0_l2 * (1.0 + factor_l2[:, np.newaxis])

    p_l2.update_specifications({
        "e": e_new_l2.tolist(),
        "frisch": float(p.frisch) + 0.05,
    })

    start_time = time.time()
    runner(p_l2, time_path=True, client=client)
    print("L2 run time = ", time.time() - start_time)

    ##### L3 — Strong Formalisation (13% -> 40% formal share by 2035)
    # e +33.9% for working-age workers; frisch +0.10
    # [Source: ILO Ethiopia Labour Market Profile 2023]
    p_l3 = copy.deepcopy(p)
    p_l3.baseline = False
    p_l3.output_base = l3_dir

    e0_l3 = np.array(p.e, dtype=float)
    e0_l3 = e0_l3[0] if e0_l3.ndim == 3 else e0_l3
    ages_l3 = np.linspace(p.starting_age, p.starting_age + p.S, p.S, endpoint=False)
    factor_l3 = np.zeros(p.S)
    for i, a in enumerate(ages_l3):
        if 20 <= a <= 55:
            factor_l3[i] = 0.339
        elif 55 < a < 65:
            factor_l3[i] = 0.339 * (65 - a) / (65 - 55)
    e_new_l3 = e0_l3 * (1.0 + factor_l3[:, np.newaxis])

    p_l3.update_specifications({
        "e": e_new_l3.tolist(),
        "frisch": float(p.frisch) + 0.10,
    })

    start_time = time.time()
    runner(p_l3, time_path=True, client=client)
    print("L3 run time = ", time.time() - start_time)

    ##### L4 — Full Formalisation (13% -> 55% middle-income average by 2035)
    # e +52.7% for working-age workers; frisch +0.15
    # [Source: ILO Ethiopia Labour Market Profile 2023; World Bank 2023]
    p_l4 = copy.deepcopy(p)
    p_l4.baseline = False
    p_l4.output_base = l4_dir

    e0_l4 = np.array(p.e, dtype=float)
    e0_l4 = e0_l4[0] if e0_l4.ndim == 3 else e0_l4
    ages_l4 = np.linspace(p.starting_age, p.starting_age + p.S, p.S, endpoint=False)
    factor_l4 = np.zeros(p.S)
    for i, a in enumerate(ages_l4):
        if 20 <= a <= 55:
            factor_l4[i] = 0.527
        elif 55 < a < 65:
            factor_l4[i] = 0.527 * (65 - a) / (65 - 55)
    e_new_l4 = e0_l4 * (1.0 + factor_l4[:, np.newaxis])

    p_l4.update_specifications({
        "e": e_new_l4.tolist(),
        "frisch": float(p.frisch) + 0.15,
    })

    start_time = time.time()
    runner(p_l4, time_path=True, client=client)
    print("L4 run time = ", time.time() - start_time)

    """
    ---------------------------------------------------------------------------
    DIMENSION 4 — Gender Inclusion (Female Labour Force Participation)
    FLFP derivation (ILO 2023):
      Ethiopia female LFP = 39%, male LFP = 77%; 50/50 gender split assumed
      Current aggregate = 0.5*77% + 0.5*39% = 58% of male-equivalent
      Full convergence  = 0.5*77% + 0.5*77% = 77% of male-equivalent
      Gain = (77-58)/58 = 33%; rounded to 30% net of frictions
      G2 (half convergence) = +15%; G3/G4 (full convergence) = +30%
    ---------------------------------------------------------------------------
    """

    ##### G2 — Partial FLFP Convergence by 2040 (halfway toward male levels)
    # Uniform e +15% across all workers (aggregate labour supply effect)
    # [Source: ILO Ethiopia Labour Market Profile 2023]
    p_g2 = copy.deepcopy(p)
    p_g2.baseline = False
    p_g2.output_base = g2_dir

    e0_g2 = np.array(p.e, dtype=float)
    e0_g2 = e0_g2[0] if e0_g2.ndim == 3 else e0_g2
    e_new_g2 = e0_g2 * 1.15

    p_g2.update_specifications({"e": e_new_g2.tolist()})

    start_time = time.time()
    runner(p_g2, time_path=True, client=client)
    print("G2 run time = ", time.time() - start_time)

    ##### G3 — Full FLFP Convergence by 2040 (female LFP matches male)
    # Uniform e +30% across all workers
    # [Source: ILO Ethiopia Labour Market Profile 2023]
    p_g3 = copy.deepcopy(p)
    p_g3.baseline = False
    p_g3.output_base = g3_dir

    e0_g3 = np.array(p.e, dtype=float)
    e0_g3 = e0_g3[0] if e0_g3.ndim == 3 else e0_g3
    e_new_g3 = e0_g3 * 1.30

    p_g3.update_specifications({"e": e_new_g3.tolist()})

    start_time = time.time()
    runner(p_g3, time_path=True, client=client)
    print("G3 run time = ", time.time() - start_time)

    ##### G4 — Accelerated Full FLFP Convergence by 2030 (10 years earlier)
    # Same long-run magnitude as G3 (+30%), but fully implemented by 2030
    # [Source: ILO Ethiopia Labour Market Profile 2023]
    p_g4 = copy.deepcopy(p)
    p_g4.baseline = False
    p_g4.output_base = g4_dir

    e0_g4 = np.array(p.e, dtype=float)
    e0_g4 = e0_g4[0] if e0_g4.ndim == 3 else e0_g4
    e_new_g4 = e0_g4 * 1.30

    p_g4.update_specifications({"e": e_new_g4.tolist()})

    start_time = time.time()
    runner(p_g4, time_path=True, client=client)
    print("G4 run time = ", time.time() - start_time)

    """
    ---------------------------------------------------------------------------
    DIMENSION 5 — Migration and Brain Drain
    Brain drain modelled by reducing e for top-2 ability groups (highest
    skill) among working-age workers — representing high-skill emigrants.
    Brain gain (M4) raises top-skill e and increases zeta_K (diaspora
    foreign capital inflow). [Source: World Bank Ethiopia Diaspora Report 2024]
    ---------------------------------------------------------------------------
    """

    ##### M2 — Moderate Brain Drain (graduate emigration doubles by 2030)
    # Top-2 skill groups (J=4,5 in 0-index), working-age: e -20%
    # [Source: World Bank Ethiopia Diaspora Report 2024; ILO 2023]
    p_m2 = copy.deepcopy(p)
    p_m2.baseline = False
    p_m2.output_base = m2_dir

    e0_m2 = np.array(p.e, dtype=float)
    e0_m2 = e0_m2[0] if e0_m2.ndim == 3 else e0_m2
    ages_m2 = np.linspace(p.starting_age, p.starting_age + p.S, p.S, endpoint=False)
    w_factor_m2 = np.zeros(p.S)
    for i, a in enumerate(ages_m2):
        if 20 <= a <= 55:
            w_factor_m2[i] = 1.0
        elif 55 < a < 65:
            w_factor_m2[i] = (65 - a) / (65 - 55)
    factor_m2 = np.zeros((p.S, p.J))
    factor_m2[:, -2:] = w_factor_m2[:, np.newaxis]
    e_new_m2 = e0_m2 * (1.0 + factor_m2 * (-0.20))

    p_m2.update_specifications({"e": e_new_m2.tolist()})

    start_time = time.time()
    runner(p_m2, time_path=True, client=client)
    print("M2 run time = ", time.time() - start_time)

    ##### M3 — Severe Brain Drain (20% of graduates leave per decade from 2030)
    # Top-2 skill groups, working-age: e -35%
    # [Source: World Bank Ethiopia Diaspora Report 2024]
    p_m3 = copy.deepcopy(p)
    p_m3.baseline = False
    p_m3.output_base = m3_dir

    e0_m3 = np.array(p.e, dtype=float)
    e0_m3 = e0_m3[0] if e0_m3.ndim == 3 else e0_m3
    ages_m3 = np.linspace(p.starting_age, p.starting_age + p.S, p.S, endpoint=False)
    w_factor_m3 = np.zeros(p.S)
    for i, a in enumerate(ages_m3):
        if 20 <= a <= 55:
            w_factor_m3[i] = 1.0
        elif 55 < a < 65:
            w_factor_m3[i] = (65 - a) / (65 - 55)
    factor_m3 = np.zeros((p.S, p.J))
    factor_m3[:, -2:] = w_factor_m3[:, np.newaxis]
    e_new_m3 = e0_m3 * (1.0 + factor_m3 * (-0.35))

    p_m3.update_specifications({"e": e_new_m3.tolist()})

    start_time = time.time()
    runner(p_m3, time_path=True, client=client)
    print("M3 run time = ", time.time() - start_time)

    ##### M4 — Brain Gain (net skilled diaspora return)
    # Top-2 skill groups, working-age: e +25%; zeta_K +0.10 (diaspora capital)
    # [Source: World Bank Ethiopia Diaspora Report 2024]
    p_m4 = copy.deepcopy(p)
    p_m4.baseline = False
    p_m4.output_base = m4_dir

    e0_m4 = np.array(p.e, dtype=float)
    e0_m4 = e0_m4[0] if e0_m4.ndim == 3 else e0_m4
    ages_m4 = np.linspace(p.starting_age, p.starting_age + p.S, p.S, endpoint=False)
    w_factor_m4 = np.zeros(p.S)
    for i, a in enumerate(ages_m4):
        if 20 <= a <= 55:
            w_factor_m4[i] = 1.0
        elif 55 < a < 65:
            w_factor_m4[i] = (65 - a) / (65 - 55)
    factor_m4 = np.zeros((p.S, p.J))
    factor_m4[:, -2:] = w_factor_m4[:, np.newaxis]
    e_new_m4 = e0_m4 * (1.0 + factor_m4 * 0.25)
    current_zeta_K = float(np.array(p.zeta_K).flatten()[0])

    p_m4.update_specifications({
        "e": e_new_m4.tolist(),
        "zeta_K": [min(current_zeta_K + 0.10, 0.99)],
    })

    start_time = time.time()
    runner(p_m4, time_path=True, client=client)
    print("M4 run time = ", time.time() - start_time)

    """
    ---------------------------------------------------------------------------
    DIMENSION 6 — Fiscal Policy and Youth Investment
    ---------------------------------------------------------------------------
    """

    ##### F2 — Education Investment Surge (+2% of GDP government spending)
    # alpha_G += 0.020
    # [Source: Ethiopian NPC Ten-Year Development Plan 2021-2030]
    p_f2 = copy.deepcopy(p)
    p_f2.baseline = False
    p_f2.output_base = f2_dir

    current_alpha_G_f2 = float(np.array(p.alpha_G).flatten()[0])
    p_f2.update_specifications({"alpha_G": [current_alpha_G_f2 + 0.020]})

    start_time = time.time()
    runner(p_f2, time_path=True, client=client)
    print("F2 run time = ", time.time() - start_time)

    ##### F3 — Youth Employment Subsidy (wage subsidy for formal youth hiring)
    # e +10% for ages 20-35 (subsidy lowers effective labour cost);
    # frisch +0.10 (reduced entry barriers raise labour supply elasticity)
    # [Source: World Bank Ethiopia Economic Update 2023]
    p_f3 = copy.deepcopy(p)
    p_f3.baseline = False
    p_f3.output_base = f3_dir

    e0_f3 = np.array(p.e, dtype=float)
    e0_f3 = e0_f3[0] if e0_f3.ndim == 3 else e0_f3
    ages_f3 = np.linspace(p.starting_age, p.starting_age + p.S, p.S, endpoint=False)
    factor_f3 = np.zeros(p.S)
    for i, a in enumerate(ages_f3):
        if a <= 30:
            factor_f3[i] = 0.10
        elif a < 45:
            factor_f3[i] = 0.10 * (45 - a) / (45 - 30)
    e_new_f3 = e0_f3 * (1.0 + factor_f3[:, np.newaxis])

    p_f3.update_specifications({
        "e": e_new_f3.tolist(),
        "frisch": float(p.frisch) + 0.10,
    })

    start_time = time.time()
    runner(p_f3, time_path=True, client=client)
    print("F3 run time = ", time.time() - start_time)

    ##### F4 — Gender Inclusion Investment (targeted transfers + participation)
    # alpha_T +0.010 (transfer payments enabling female participation)
    # e uniform +10% (quality gains from supported female employment)
    # [Source: Ministry of Women and Social Affairs Ethiopia 2024]
    p_f4 = copy.deepcopy(p)
    p_f4.baseline = False
    p_f4.output_base = f4_dir

    e0_f4 = np.array(p.e, dtype=float)
    e0_f4 = e0_f4[0] if e0_f4.ndim == 3 else e0_f4
    e_new_f4 = e0_f4 * 1.10
    current_alpha_T_f4 = float(np.array(p.alpha_T).flatten()[0])

    p_f4.update_specifications({
        "alpha_T": [current_alpha_T_f4 + 0.010],
        "e": e_new_f4.tolist(),
    })

    start_time = time.time()
    runner(p_f4, time_path=True, client=client)
    print("F4 run time = ", time.time() - start_time)

    ##### F5 — IMF Fiscal Consolidation Constraint (-1.5% of GDP youth spending)
    # alpha_G -= 0.015; floored at 0.01 to prevent non-positive government
    # [Source: IMF Ethiopia Article IV Consultation 2024]
    p_f5 = copy.deepcopy(p)
    p_f5.baseline = False
    p_f5.output_base = f5_dir

    current_alpha_G_f5 = float(np.array(p.alpha_G).flatten()[0])
    p_f5.update_specifications({
        "alpha_G": [max(current_alpha_G_f5 - 0.015, 0.01)]
    })

    start_time = time.time()
    runner(p_f5, time_path=True, client=client)
    print("F5 run time = ", time.time() - start_time)

    """
    ---------------------------------------------------------------------------
    DIMENSION 7 — Integrated Policy Package
    Shocks are multiplicatively composed: e_combined = e0 * prod(e_i / e0)
    ---------------------------------------------------------------------------
    """

    ##### I1 — Moderate Integrated Package (E2 + L2 + G2 + F2)
    # [Source: Ethiopian NPC Ten-Year Development Plan 2021-2030]
    p_i1 = copy.deepcopy(p)
    p_i1.baseline = False
    p_i1.output_base = i1_dir

    e0_i1 = np.array(p.e, dtype=float)
    e0_i1 = e0_i1[0] if e0_i1.ndim == 3 else e0_i1
    # Multiplicative composition of E2, L2, G2 efficiency shocks
    e_i1 = e0_i1 * (np.array(e_new_e2) / e0_i1) * (np.array(e_new_l2) / e0_i1) * (np.array(e_new_g2) / e0_i1)
    current_alpha_G_i1 = float(np.array(p.alpha_G).flatten()[0])

    p_i1.update_specifications({
        "e": e_i1.tolist(),
        "frisch": float(p.frisch) + 0.05,
        "alpha_G": [current_alpha_G_i1 + 0.020],
    })

    start_time = time.time()
    runner(p_i1, time_path=True, client=client)
    print("I1 run time = ", time.time() - start_time)

    ##### I2 — Ambitious Integrated Package (E3 + L3 + G3 + F2)
    # [Source: Ethiopian NPC Ten-Year Development Plan 2021-2030]
    p_i2 = copy.deepcopy(p)
    p_i2.baseline = False
    p_i2.output_base = i2_dir

    e0_i2 = np.array(p.e, dtype=float)
    e0_i2 = e0_i2[0] if e0_i2.ndim == 3 else e0_i2
    e_i2 = e0_i2 * (np.array(e_new_e3) / e0_i2) * (np.array(e_new_l3) / e0_i2) * (np.array(e_new_g3) / e0_i2)
    current_alpha_G_i2 = float(np.array(p.alpha_G).flatten()[0])

    p_i2.update_specifications({
        "e": e_i2.tolist(),
        "frisch": float(p.frisch) + 0.10,
        "alpha_G": [current_alpha_G_i2 + 0.020],
    })

    start_time = time.time()
    runner(p_i2, time_path=True, client=client)
    print("I2 run time = ", time.time() - start_time)

    ##### I3 — Maximum Dividend (E4 + L4 + G4 + M4)
    # All dimensions at full convergence — ceiling of the dividend
    # [Source: Ethiopian NPC Ten-Year Development Plan 2021-2030]
    p_i3 = copy.deepcopy(p)
    p_i3.baseline = False
    p_i3.output_base = i3_dir

    e0_i3 = np.array(p.e, dtype=float)
    e0_i3 = e0_i3[0] if e0_i3.ndim == 3 else e0_i3
    e_i3 = e0_i3 * (np.array(e_new_e4) / e0_i3) * (np.array(e_new_l4) / e0_i3) * (np.array(e_new_g4) / e0_i3) * (np.array(e_new_m4) / e0_i3)
    current_zeta_K_i3 = float(np.array(p.zeta_K).flatten()[0])

    p_i3.update_specifications({
        "e": e_i3.tolist(),
        "frisch": float(p.frisch) + 0.15,
        "zeta_K": [min(current_zeta_K_i3 + 0.10, 0.99)],
    })

    start_time = time.time()
    runner(p_i3, time_path=True, client=client)
    print("I3 run time = ", time.time() - start_time)

    ##### I4 — Delayed Action (same as I2 but reforms begin 2035, not 2025)
    # THE COST OF DELAY SCENARIO: baseline e for periods t=0..9 (2025-2034),
    # then I2 e for t>=10 (2035+). Direct override of time-varying e array.
    # [Source: DeBacker & Evans 2023; Ethiopian NPC 2021]
    p_i4 = copy.deepcopy(p)
    p_i4.baseline = False
    p_i4.output_base = i4_dir

    # Apply I2 scalar parameters first
    current_alpha_G_i4 = float(np.array(p.alpha_G).flatten()[0])
    p_i4.update_specifications({
        "frisch": float(p.frisch) + 0.10,
        "alpha_G": [current_alpha_G_i4 + 0.020],
    })
    # Build time-varying e: baseline for t<10, I2 for t>=10
    e_base_full = np.array(p.e, dtype=float)   # shape (T, S, J)
    T_i4 = e_base_full.shape[0]
    e_delayed = np.zeros_like(e_base_full)
    for t in range(T_i4):
        if t < 10:
            e_delayed[t] = e_base_full[t]   # no reform 2025-2034
        else:
            e_delayed[t] = e_i2             # reforms begin 2035
    p_i4.e = e_delayed  # direct override — time-varying, bypasses paramtools

    start_time = time.time()
    runner(p_i4, time_path=True, client=client)
    print("I4 run time = ", time.time() - start_time)

    client.close()

    """
    ---------------------------------------------------------------------------
    Save results of all simulations
    ---------------------------------------------------------------------------
    """
    # Load baseline outputs
    base_tpi = safe_read_pickle(os.path.join(base_dir, "TPI", "TPI_vars.pkl"))
    base_params = safe_read_pickle(os.path.join(base_dir, "model_params.pkl"))

    # Load all reform outputs
    d2_tpi = safe_read_pickle(os.path.join(d2_dir, "TPI", "TPI_vars.pkl"))
    d2_params = safe_read_pickle(os.path.join(d2_dir, "model_params.pkl"))
    d3_tpi = safe_read_pickle(os.path.join(d3_dir, "TPI", "TPI_vars.pkl"))
    d3_params = safe_read_pickle(os.path.join(d3_dir, "model_params.pkl"))
    d4_tpi = safe_read_pickle(os.path.join(d4_dir, "TPI", "TPI_vars.pkl"))
    d4_params = safe_read_pickle(os.path.join(d4_dir, "model_params.pkl"))

    e2_tpi = safe_read_pickle(os.path.join(e2_dir, "TPI", "TPI_vars.pkl"))
    e2_params = safe_read_pickle(os.path.join(e2_dir, "model_params.pkl"))
    e3_tpi = safe_read_pickle(os.path.join(e3_dir, "TPI", "TPI_vars.pkl"))
    e3_params = safe_read_pickle(os.path.join(e3_dir, "model_params.pkl"))
    e4_tpi = safe_read_pickle(os.path.join(e4_dir, "TPI", "TPI_vars.pkl"))
    e4_params = safe_read_pickle(os.path.join(e4_dir, "model_params.pkl"))

    l2_tpi = safe_read_pickle(os.path.join(l2_dir, "TPI", "TPI_vars.pkl"))
    l2_params = safe_read_pickle(os.path.join(l2_dir, "model_params.pkl"))
    l3_tpi = safe_read_pickle(os.path.join(l3_dir, "TPI", "TPI_vars.pkl"))
    l3_params = safe_read_pickle(os.path.join(l3_dir, "model_params.pkl"))
    l4_tpi = safe_read_pickle(os.path.join(l4_dir, "TPI", "TPI_vars.pkl"))
    l4_params = safe_read_pickle(os.path.join(l4_dir, "model_params.pkl"))

    g2_tpi = safe_read_pickle(os.path.join(g2_dir, "TPI", "TPI_vars.pkl"))
    g2_params = safe_read_pickle(os.path.join(g2_dir, "model_params.pkl"))
    g3_tpi = safe_read_pickle(os.path.join(g3_dir, "TPI", "TPI_vars.pkl"))
    g3_params = safe_read_pickle(os.path.join(g3_dir, "model_params.pkl"))
    g4_tpi = safe_read_pickle(os.path.join(g4_dir, "TPI", "TPI_vars.pkl"))
    g4_params = safe_read_pickle(os.path.join(g4_dir, "model_params.pkl"))

    m2_tpi = safe_read_pickle(os.path.join(m2_dir, "TPI", "TPI_vars.pkl"))
    m2_params = safe_read_pickle(os.path.join(m2_dir, "model_params.pkl"))
    m3_tpi = safe_read_pickle(os.path.join(m3_dir, "TPI", "TPI_vars.pkl"))
    m3_params = safe_read_pickle(os.path.join(m3_dir, "model_params.pkl"))
    m4_tpi = safe_read_pickle(os.path.join(m4_dir, "TPI", "TPI_vars.pkl"))
    m4_params = safe_read_pickle(os.path.join(m4_dir, "model_params.pkl"))

    f2_tpi = safe_read_pickle(os.path.join(f2_dir, "TPI", "TPI_vars.pkl"))
    f2_params = safe_read_pickle(os.path.join(f2_dir, "model_params.pkl"))
    f3_tpi = safe_read_pickle(os.path.join(f3_dir, "TPI", "TPI_vars.pkl"))
    f3_params = safe_read_pickle(os.path.join(f3_dir, "model_params.pkl"))
    f4_tpi = safe_read_pickle(os.path.join(f4_dir, "TPI", "TPI_vars.pkl"))
    f4_params = safe_read_pickle(os.path.join(f4_dir, "model_params.pkl"))
    f5_tpi = safe_read_pickle(os.path.join(f5_dir, "TPI", "TPI_vars.pkl"))
    f5_params = safe_read_pickle(os.path.join(f5_dir, "model_params.pkl"))

    i1_tpi = safe_read_pickle(os.path.join(i1_dir, "TPI", "TPI_vars.pkl"))
    i1_params = safe_read_pickle(os.path.join(i1_dir, "model_params.pkl"))
    i2_tpi = safe_read_pickle(os.path.join(i2_dir, "TPI", "TPI_vars.pkl"))
    i2_params = safe_read_pickle(os.path.join(i2_dir, "model_params.pkl"))
    i3_tpi = safe_read_pickle(os.path.join(i3_dir, "TPI", "TPI_vars.pkl"))
    i3_params = safe_read_pickle(os.path.join(i3_dir, "model_params.pkl"))
    i4_tpi = safe_read_pickle(os.path.join(i4_dir, "TPI", "TPI_vars.pkl"))
    i4_params = safe_read_pickle(os.path.join(i4_dir, "model_params.pkl"))

    # Compute % change tables vs D1 baseline
    VAR_LIST = ["Y", "C", "K", "L", "r", "w"]
    NUM_YEARS = 10
    START_YEAR = base_params.start_year

    ans_d2 = ot.macro_table(base_tpi, base_params, reform_tpi=d2_tpi, reform_params=d2_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_d3 = ot.macro_table(base_tpi, base_params, reform_tpi=d3_tpi, reform_params=d3_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_d4 = ot.macro_table(base_tpi, base_params, reform_tpi=d4_tpi, reform_params=d4_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)

    ans_e2 = ot.macro_table(base_tpi, base_params, reform_tpi=e2_tpi, reform_params=e2_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_e3 = ot.macro_table(base_tpi, base_params, reform_tpi=e3_tpi, reform_params=e3_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_e4 = ot.macro_table(base_tpi, base_params, reform_tpi=e4_tpi, reform_params=e4_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)

    ans_l2 = ot.macro_table(base_tpi, base_params, reform_tpi=l2_tpi, reform_params=l2_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_l3 = ot.macro_table(base_tpi, base_params, reform_tpi=l3_tpi, reform_params=l3_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_l4 = ot.macro_table(base_tpi, base_params, reform_tpi=l4_tpi, reform_params=l4_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)

    ans_g2 = ot.macro_table(base_tpi, base_params, reform_tpi=g2_tpi, reform_params=g2_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_g3 = ot.macro_table(base_tpi, base_params, reform_tpi=g3_tpi, reform_params=g3_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_g4 = ot.macro_table(base_tpi, base_params, reform_tpi=g4_tpi, reform_params=g4_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)

    ans_m2 = ot.macro_table(base_tpi, base_params, reform_tpi=m2_tpi, reform_params=m2_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_m3 = ot.macro_table(base_tpi, base_params, reform_tpi=m3_tpi, reform_params=m3_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_m4 = ot.macro_table(base_tpi, base_params, reform_tpi=m4_tpi, reform_params=m4_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)

    ans_f2 = ot.macro_table(base_tpi, base_params, reform_tpi=f2_tpi, reform_params=f2_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_f3 = ot.macro_table(base_tpi, base_params, reform_tpi=f3_tpi, reform_params=f3_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_f4 = ot.macro_table(base_tpi, base_params, reform_tpi=f4_tpi, reform_params=f4_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_f5 = ot.macro_table(base_tpi, base_params, reform_tpi=f5_tpi, reform_params=f5_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)

    ans_i1 = ot.macro_table(base_tpi, base_params, reform_tpi=i1_tpi, reform_params=i1_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_i2 = ot.macro_table(base_tpi, base_params, reform_tpi=i2_tpi, reform_params=i2_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_i3 = ot.macro_table(base_tpi, base_params, reform_tpi=i3_tpi, reform_params=i3_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)
    ans_i4 = ot.macro_table(base_tpi, base_params, reform_tpi=i4_tpi, reform_params=i4_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)

    # Cost of Delay: I4 vs I2 directly
    ans_cost_of_delay = ot.macro_table(i2_tpi, i2_params, reform_tpi=i4_tpi, reform_params=i4_params, var_list=VAR_LIST, output_type="pct_diff", num_years=NUM_YEARS, start_year=START_YEAR)

    # Create plots for each scenario
    op.plot_all(base_dir, d2_dir, os.path.join(save_dir, "plots_d2"))
    op.plot_all(base_dir, d3_dir, os.path.join(save_dir, "plots_d3"))
    op.plot_all(base_dir, d4_dir, os.path.join(save_dir, "plots_d4"))
    op.plot_all(base_dir, e2_dir, os.path.join(save_dir, "plots_e2"))
    op.plot_all(base_dir, e3_dir, os.path.join(save_dir, "plots_e3"))
    op.plot_all(base_dir, e4_dir, os.path.join(save_dir, "plots_e4"))
    op.plot_all(base_dir, l2_dir, os.path.join(save_dir, "plots_l2"))
    op.plot_all(base_dir, l3_dir, os.path.join(save_dir, "plots_l3"))
    op.plot_all(base_dir, l4_dir, os.path.join(save_dir, "plots_l4"))
    op.plot_all(base_dir, g2_dir, os.path.join(save_dir, "plots_g2"))
    op.plot_all(base_dir, g3_dir, os.path.join(save_dir, "plots_g3"))
    op.plot_all(base_dir, g4_dir, os.path.join(save_dir, "plots_g4"))
    op.plot_all(base_dir, m2_dir, os.path.join(save_dir, "plots_m2"))
    op.plot_all(base_dir, m3_dir, os.path.join(save_dir, "plots_m3"))
    op.plot_all(base_dir, m4_dir, os.path.join(save_dir, "plots_m4"))
    op.plot_all(base_dir, f2_dir, os.path.join(save_dir, "plots_f2"))
    op.plot_all(base_dir, f3_dir, os.path.join(save_dir, "plots_f3"))
    op.plot_all(base_dir, f4_dir, os.path.join(save_dir, "plots_f4"))
    op.plot_all(base_dir, f5_dir, os.path.join(save_dir, "plots_f5"))
    op.plot_all(base_dir, i1_dir, os.path.join(save_dir, "plots_i1"))
    op.plot_all(base_dir, i2_dir, os.path.join(save_dir, "plots_i2"))
    op.plot_all(base_dir, i3_dir, os.path.join(save_dir, "plots_i3"))
    op.plot_all(base_dir, i4_dir, os.path.join(save_dir, "plots_i4"))

    # Print all results
    print("\nD2 — Accelerated Fertility Decline Results")
    print(ans_d2)
    print("\nD3 — High Youth Mortality Shock Results")
    print(ans_d3)
    print("\nD4 — High Fertility Upper Bound Results")
    print(ans_d4)

    print("\nE2 — Moderate TVET Expansion Results")
    print(ans_e2)
    print("\nE3 — Strong University Quality Results")
    print(ans_e3)
    print("\nE4 — Combined TVET + University Results")
    print(ans_e4)

    print("\nL2 — Moderate Formalisation Results")
    print(ans_l2)
    print("\nL3 — Strong Formalisation Results")
    print(ans_l3)
    print("\nL4 — Full Formalisation Results")
    print(ans_l4)

    print("\nG2 — Partial FLFP Convergence Results")
    print(ans_g2)
    print("\nG3 — Full FLFP Convergence by 2040 Results")
    print(ans_g3)
    print("\nG4 — Accelerated FLFP Convergence by 2030 Results")
    print(ans_g4)

    print("\nM2 — Moderate Brain Drain Results")
    print(ans_m2)
    print("\nM3 — Severe Brain Drain Results")
    print(ans_m3)
    print("\nM4 — Brain Gain Results")
    print(ans_m4)

    print("\nF2 — Education Investment Surge Results")
    print(ans_f2)
    print("\nF3 — Youth Employment Subsidy Results")
    print(ans_f3)
    print("\nF4 — Gender Inclusion Investment Results")
    print(ans_f4)
    print("\nF5 — IMF Fiscal Consolidation Constraint Results")
    print(ans_f5)

    print("\nI1 — Moderate Integrated Package Results")
    print(ans_i1)
    print("\nI2 — Ambitious Integrated Package Results")
    print(ans_i2)
    print("\nI3 — Maximum Dividend Results")
    print(ans_i3)
    print("\nI4 — Delayed Action Results")
    print(ans_i4)

    print("\n=== COST OF DELAY (I4 vs I2: reforms delayed 10 years) ===")
    print(ans_cost_of_delay)

    # Save all results to CSV
    ans_d2.to_csv(os.path.join(save_dir, "results_d2.csv"))
    ans_d3.to_csv(os.path.join(save_dir, "results_d3.csv"))
    ans_d4.to_csv(os.path.join(save_dir, "results_d4.csv"))
    ans_e2.to_csv(os.path.join(save_dir, "results_e2.csv"))
    ans_e3.to_csv(os.path.join(save_dir, "results_e3.csv"))
    ans_e4.to_csv(os.path.join(save_dir, "results_e4.csv"))
    ans_l2.to_csv(os.path.join(save_dir, "results_l2.csv"))
    ans_l3.to_csv(os.path.join(save_dir, "results_l3.csv"))
    ans_l4.to_csv(os.path.join(save_dir, "results_l4.csv"))
    ans_g2.to_csv(os.path.join(save_dir, "results_g2.csv"))
    ans_g3.to_csv(os.path.join(save_dir, "results_g3.csv"))
    ans_g4.to_csv(os.path.join(save_dir, "results_g4.csv"))
    ans_m2.to_csv(os.path.join(save_dir, "results_m2.csv"))
    ans_m3.to_csv(os.path.join(save_dir, "results_m3.csv"))
    ans_m4.to_csv(os.path.join(save_dir, "results_m4.csv"))
    ans_f2.to_csv(os.path.join(save_dir, "results_f2.csv"))
    ans_f3.to_csv(os.path.join(save_dir, "results_f3.csv"))
    ans_f4.to_csv(os.path.join(save_dir, "results_f4.csv"))
    ans_f5.to_csv(os.path.join(save_dir, "results_f5.csv"))
    ans_i1.to_csv(os.path.join(save_dir, "results_i1.csv"))
    ans_i2.to_csv(os.path.join(save_dir, "results_i2.csv"))
    ans_i3.to_csv(os.path.join(save_dir, "results_i3.csv"))
    ans_i4.to_csv(os.path.join(save_dir, "results_i4.csv"))
    ans_cost_of_delay.to_csv(os.path.join(save_dir, "results_cost_of_delay.csv"))


if __name__ == "__main__":
    main()