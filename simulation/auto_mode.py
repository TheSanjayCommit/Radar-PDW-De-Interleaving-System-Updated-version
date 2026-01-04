import streamlit as st
import numpy as np
import pandas as pd
import os

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

np.random.seed(42)
def toa_us_to_hms(toa_us):
    total_seconds = int(toa_us // 1_000_000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# =================================================
# SESSION STATE
# =================================================
if "global_time_us" not in st.session_state:
    st.session_state.global_time_us = 0.0

if "pdw_buffer" not in st.session_state:
    st.session_state.pdw_buffer = []

if "auto_running" not in st.session_state:
    st.session_state.auto_running = False


# =================================================
# AUTO MODE UI
# =================================================
def auto_mode_ui():

    st.header("Auto Mode – PDW Simulation (Continuous Time)")
    st.info("PDWs are generated in 2-second continuous windows")

    cfg = st.session_state.auto_config

    num_emitters = st.number_input(
        "Number of Emitters", 1, 100, cfg.get("num_emitters", 10), step=1
    )
    pulses_per_emitter = st.number_input(
        "Pulses per Emitter (per 2s window)", 1, 1000, cfg.get("pulses_per_emitter", 20)
    )

    cfg["num_emitters"] = num_emitters
    cfg["pulses_per_emitter"] = pulses_per_emitter

    # -----------------------------
    # EMITTER TYPE DISTRIBUTION
    # -----------------------------
    st.subheader("Emitter Type Distribution (%)")

    fixed_pct = st.number_input("Fixed Emitters (%)", 0, 100, cfg.get("fixed_pct", 60))
    agile_pct = st.number_input("Frequency Agile Emitters (%)", 0, 100, cfg.get("agile_pct", 25))
    stagger_pct = st.number_input("Staggered PRI Emitters (%)", 0, 100, cfg.get("stagger_pct", 15))

    if fixed_pct + agile_pct + stagger_pct != 100:
        st.error("Emitter percentages must sum to 100")
        return

    cfg.update({
        "fixed_pct": fixed_pct,
        "agile_pct": agile_pct,
        "stagger_pct": stagger_pct
    })

    # -----------------------------
    # PARAMETER RANGES
    # -----------------------------
    st.subheader("Parameter Ranges")

    f_min = st.number_input("Frequency Min (MHz)", 500.0, 40000.0, cfg.get("f_min", 8000.0))
    f_max = st.number_input("Frequency Max (MHz)", 500.0, 40000.0, cfg.get("f_max", 12000.0))

    pri_min = st.number_input("PRI Min (µs)", 2.0, 20000.0, cfg.get("pri_min", 2000.0))
    pri_max = st.number_input("PRI Max (µs)", 2.0, 20000.0, cfg.get("pri_max", 6000.0))

    pw_min = st.number_input("Pulse Width Min (µs)", 0.01, 1000.0, cfg.get("pw_min", 10.0))
    pw_max = st.number_input("Pulse Width Max (µs)", 0.01, 1000.0, cfg.get("pw_max", 50.0))

    amp_min = st.number_input("Amplitude Min (dB)", -200.0, 10.0, cfg.get("amp_min", -80.0))
    amp_max = st.number_input("Amplitude Max (dB)", -200.0, 10.0, cfg.get("amp_max", -30.0))

    doa_min = st.number_input("DOA Min (deg)", 0.0, 360.0, cfg.get("doa_min", 0.0))
    doa_max = st.number_input("DOA Max (deg)", 0.0, 360.0, cfg.get("doa_max", 360.0))

    # -----------------------------
    # SIMULATION CONTROL
    # -----------------------------
    st.subheader("Simulation Control")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("▶ Start / Generate"):
            st.session_state.auto_running = True

    with c2:
        if st.button("⏸ Pause"):
            st.session_state.auto_running = False

    with c3:
        if st.button("⏹ Reset"):
            st.session_state.auto_running = False
            st.session_state.global_time_us = 0.0
            st.session_state.pdw_buffer = []
            st.success("Auto mode reset")

    # -----------------------------
    # GENERATE PDWs
    # -----------------------------
    if st.session_state.auto_running:

        df_new = generate_pdws_2s(
            num_emitters, pulses_per_emitter,
            fixed_pct, agile_pct, stagger_pct,
            f_min, f_max, pri_min, pri_max,
            pw_min, pw_max, amp_min, amp_max,
            doa_min, doa_max
        )

        out_dir = st.session_state.get("user_output_dir", OUTPUT_DIR)
        st.session_state.pdw_buffer.extend(df_new.to_dict("records"))


        df_all = pd.DataFrame(st.session_state.pdw_buffer)

        df_all = df_all.sort_values("toa_us").round(2)
        df_all["toa_hms"] = df_all["toa_us"].apply(toa_us_to_hms)

        df_all.to_csv(f"{out_dir}/pdw_interleaved.csv", index=False)

        st.session_state.auto_running = False
        st.success(f"Generated 2 seconds of PDWs (Total: {len(df_all)})")
        st.dataframe(df_all.tail(20))


# =================================================
# REALISTIC PDW GENERATION (FIXED)
# =================================================
def generate_pdws_2s(num_emitters, pulses_per_emitter,
                     fixed_pct, agile_pct, stagger_pct,
                     f_min, f_max, pri_min, pri_max,
                     pw_min, pw_max, amp_min, amp_max,
                     doa_min, doa_max):

    rows = []

    window_start = st.session_state.global_time_us
    window_end = window_start + 2e6
    st.session_state.global_time_us = window_end

    n_fixed = int(num_emitters * fixed_pct / 100)
    n_agile = int(num_emitters * agile_pct / 100)
    n_stagger = num_emitters - n_fixed - n_agile

    emitter_types = (
        ["fixed"] * n_fixed +
        ["agile"] * n_agile +
        ["stagger"] * n_stagger
    )
    np.random.shuffle(emitter_types)

    for etype in emitter_types:

        # Base parameters (per emitter)
        base_freq = np.random.uniform(f_min, f_max)
        base_pri  = np.random.uniform(pri_min, pri_max)
        base_pw   = np.random.uniform(pw_min, pw_max)
        base_amp  = np.random.uniform(amp_min, amp_max)
        base_doa  = np.random.uniform(doa_min, doa_max)

        # Tolerances
        FREQ_TOL = 10.0
        PRI_TOL  = 0.02 * base_pri
        PW_TOL   = 0.05 * base_pw
        DOA_TOL  = 2.0
        AMP_TOL  = 1.0

        # Agile frequency modes
        if etype == "agile":
            freq_modes = np.random.uniform(base_freq - 100, base_freq + 100,
                                            np.random.randint(2, 5))
        else:
            freq_modes = [base_freq]

        # Staggered PRI
        if etype == "stagger":
            pri_modes = np.random.uniform(base_pri * 0.8, base_pri * 1.2,
                                           np.random.randint(2, 4))
        else:
            pri_modes = [base_pri]

        toa = np.random.uniform(window_start, window_end)

        for k in range(pulses_per_emitter):

            freq = freq_modes[k % len(freq_modes)] + np.random.normal(0, FREQ_TOL)
            pri  = pri_modes[k % len(pri_modes)]   + np.random.normal(0, PRI_TOL)

            rows.append({
                "freq_MHz": freq,
                "pri_us": pri,
                "pw_us": base_pw + np.random.normal(0, PW_TOL),
                "doa_deg": base_doa + np.random.normal(0, DOA_TOL),
                "amp_dB": base_amp + np.random.normal(0, AMP_TOL),
                "toa_us": toa
            })

            toa += pri
            if toa > window_end:
                break

    return pd.DataFrame(rows)
