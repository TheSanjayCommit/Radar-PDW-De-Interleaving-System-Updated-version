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

    fixed_pct = st.number_input("Fixed Emitters (%)", 0, 100, cfg.get("fixed_pct", 100))
    agile_pct = st.number_input("Frequency Agile Emitters (%)", 0, 100, cfg.get("agile_pct", 0))
    stagger_pct = st.number_input("Staggered PRI Emitters (%)", 0, 100, cfg.get("stagger_pct", 0))

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

    saved_f_min = cfg.get("f_min", 8000.0)
    f_min = st.number_input("Frequency Min (MHz)", 500.0, 40000.0, float(saved_f_min))
    cfg["f_min"] = f_min

    saved_f_max = cfg.get("f_max", 12000.0)
    f_max = st.number_input("Frequency Max (MHz)", 500.0, 40000.0, float(saved_f_max))
    cfg["f_max"] = f_max

    saved_pri_min = cfg.get("pri_min", 2000.0)
    pri_min = st.number_input("PRI Min (µs)", 2.0, 20000.0, float(saved_pri_min))
    cfg["pri_min"] = pri_min

    saved_pri_max = cfg.get("pri_max", 6000.0)
    pri_max = st.number_input("PRI Max (µs)", 2.0, 20000.0, float(saved_pri_max))
    cfg["pri_max"] = pri_max

    saved_pw_min = cfg.get("pw_min", 10.0)
    pw_min = st.number_input("Pulse Width Min (µs)", 0.01, 1000.0, float(saved_pw_min))
    cfg["pw_min"] = pw_min

    saved_pw_max = cfg.get("pw_max", 50.0)
    pw_max = st.number_input("Pulse Width Max (µs)", 0.01, 1000.0, float(saved_pw_max))
    cfg["pw_max"] = pw_max

    saved_amp_min = cfg.get("amp_min", -80.0)
    amp_min = st.number_input("Amplitude Min (dB)", -200.0, 10.0, float(saved_amp_min))
    cfg["amp_min"] = amp_min

    saved_amp_max = cfg.get("amp_max", -30.0)
    amp_max = st.number_input("Amplitude Max (dB)", -200.0, 10.0, float(saved_amp_max))
    cfg["amp_max"] = amp_max

    saved_doa_min = cfg.get("doa_min", 0.0)
    doa_min = st.number_input("DOA Min (deg)", 0.0, 360.0, float(saved_doa_min))
    cfg["doa_min"] = doa_min

    saved_doa_max = cfg.get("doa_max", 360.0)
    doa_max = st.number_input("DOA Max (deg)", 0.0, 360.0, float(saved_doa_max))
    cfg["doa_max"] = doa_max

    # -----------------------------
    # SIMULATION NOISE (JITTER)
    # -----------------------------
    st.subheader("Simulation Noise (Jitter)")
    st.caption("Controls the randomness added to the generated pulses.")
    
    saved_noise_freq = cfg.get("noise_freq", 0.0)
    noise_freq = st.number_input("Frequency Noise (±MHz)", 0.0, 50.0, float(saved_noise_freq), 0.5)
    cfg["noise_freq"] = noise_freq

    saved_noise_pri = cfg.get("noise_pri_pct", 0.0) # percent
    noise_pri = st.number_input("PRI Jitter (±%)", 0.0, 50.0, float(saved_noise_pri), 0.5)
    cfg["noise_pri_pct"] = noise_pri

    saved_noise_pw = cfg.get("noise_pw_pct", 0.0) # percent
    noise_pw = st.number_input("PW Jitter (±%)", 0.0, 50.0, float(saved_noise_pw), 0.5)
    cfg["noise_pw_pct"] = noise_pw

    saved_noise_doa = cfg.get("noise_doa", 0.0)
    noise_doa = st.number_input("DOA Noise (±deg)", 0.0, 10.0, float(saved_noise_doa), 0.5)
    cfg["noise_doa"] = noise_doa

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
        if st.button("🔴 Reset Simulation & Clear Data", type="primary", help="Clears all generated data and resets configuration."):
            st.session_state.auto_running = False
            st.session_state.global_time_us = 0.0
            st.session_state.pdw_buffer = []
            st.session_state.auto_config.clear()
            st.rerun()

    # -----------------------------
    # GENERATE PDWs
    # -----------------------------
    if st.session_state.auto_running:

        df_new = generate_pdws_2s(
            num_emitters, pulses_per_emitter,
            fixed_pct, agile_pct, stagger_pct,
            f_min, f_max, pri_min, pri_max,
            pw_min, pw_max, amp_min, amp_max,
            doa_min, doa_max,
            noise_freq, noise_pri, noise_pw, noise_doa
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
                     doa_min, doa_max,
                     n_freq, n_pri_pct, n_pw_pct, n_doa):

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

    # Create stratified/separated base parameters to prevent overlap (detected==expected)
    # 1. Generate base frequencies evenly spaced
    base_freqs = np.linspace(f_min, f_max, num_emitters + 2)[1:-1] # avoid edges
    np.random.shuffle(base_freqs) # randomize assignment
    
    # 2. Generate base PRIs evenly spaced
    base_pris = np.linspace(pri_min, pri_max, num_emitters + 2)[1:-1]
    np.random.shuffle(base_pris)

    for i, etype in enumerate(emitter_types):

        # Base parameters (per emitter)
        # Add slight jitter to the stratified base, but keeping them distinct
        base_freq = base_freqs[i] + np.random.uniform(-50, 50) 
        base_pri  = base_pris[i]  + np.random.uniform(-100, 100)
        
        base_pw   = np.random.uniform(pw_min, pw_max)
        base_amp  = np.random.uniform(amp_min, amp_max)
        base_doa  = np.random.uniform(doa_min, doa_max)

        # Tolerances
        # Tolerances (Noise)
        FREQ_TOL = n_freq
        PRI_TOL  = (n_pri_pct / 100.0) * base_pri
        PW_TOL   = (n_pw_pct / 100.0) * base_pw
        DOA_TOL  = n_doa
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

        # Start TOA near the beginning of the window to ensure pulses fit
        # allowing for some stochastic offset
        start_offset = np.random.uniform(0, pri_modes[0]) 
        toa = window_start + start_offset

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

            # if toa > window_end:
            #    break

    return pd.DataFrame(rows)
