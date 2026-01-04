import streamlit as st
import numpy as np
import pandas as pd
import os

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def toa_us_to_hms(toa_us):
    total_seconds = int(toa_us // 1_000_000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# =================================================
# MANUAL MODE UI
# =================================================
def manual_mode_ui():

    if "manual_global_time_us" not in st.session_state:
        st.session_state.manual_global_time_us = 0.0
    if "manual_pdw_buffer" not in st.session_state:
        st.session_state.manual_pdw_buffer = []
    if "manual_running" not in st.session_state:
        st.session_state.manual_running = False

    st.header("Manual Mode – PDW Simulation (Continuous Time)")
    st.info("Emitter parameters are manually configured with realistic tolerances")

    cfg = st.session_state.manual_config

    num_emitters = st.number_input(
        "Number of Emitters", 1, 20, cfg.get("num_emitters", 3)
    )
    pulses_per_emitter = st.number_input(
        "Pulses per Emitter (per 2s)", 1, 1000, cfg.get("pulses", 20)
    )

    cfg["num_emitters"] = num_emitters
    cfg["pulses"] = pulses_per_emitter

    emitters = []

    # =================================================
    # EMITTER CONFIGURATION
    # =================================================
    for i in range(num_emitters):
        st.markdown(f"### Emitter {i+1}")

        # -----------------------------
        # FREQUENCY CONFIG
        # -----------------------------
        freq_type = st.selectbox(
            "Frequency Type",
            ["Fixed", "Agile"],
            key=f"freq_type_{i}"
        )

        freqs = []
        if freq_type == "Agile":
            num_modes = st.number_input(
                "Number of Frequency Modes",
                min_value=2,
                max_value=8,      # ✅ LIMITED TO 8
                value=3,
                key=f"num_modes_{i}"
            )
            for m in range(num_modes):
                freqs.append(
                    st.number_input(
                        f"Mode {m+1} Frequency (MHz)",
                        500.0, 40000.0,
                        9000.0 + m * 50,
                        key=f"freq_{i}_{m}"
                    )
                )
        else:
            freqs.append(
                st.number_input(
                    "Base Frequency (MHz)",
                    500.0, 40000.0,
                    9000.0,
                    key=f"freq_{i}"
                )
            )

        # -----------------------------
        # PRI CONFIG
        # -----------------------------
        pri_type = st.selectbox(
            "PRI Type",
            ["Fixed", "Jittered", "Staggered"],
            key=f"pri_type_{i}"
        )

        pri_values = []

        if pri_type == "Staggered":
            num_pri = st.number_input(
                "Number of PRI Values",
                min_value=2,
                max_value=5,      # ✅ LIMITED TO 5
                value=2,
                key=f"num_pri_{i}"
            )
            for p in range(num_pri):
                pri_values.append(
                    st.number_input(
                        f"PRI {p+1} (µs)",
                        2.0, 20000.0,
                        2000.0 + p * 500,
                        key=f"pri_{i}_{p}"
                    )
                )
        else:
            pri_values.append(
                st.number_input(
                    "Base PRI (µs)",
                    2.0, 20000.0,
                    2000.0,
                    key=f"pri_{i}"
                )
            )

        # -----------------------------
        # OTHER PARAMETERS
        # -----------------------------
        pw = st.number_input(
            "Pulse Width (µs)",
            0.01, 1000.0,
            10.0,
            key=f"pw_{i}"
        )

        amp = st.number_input(
            "Amplitude (dB)",
            -200.0, 10.0,
            -60.0,
            key=f"amp_{i}"
        )

        doa = st.number_input(
            "DOA (deg)",
            0.0, 360.0,
            90.0,
            key=f"doa_{i}"
        )

        emitters.append({
            "freqs": freqs,
            "pri_type": pri_type,
            "pri_values": pri_values,
            "pw": pw,
            "amp": amp,
            "doa": doa
        })

    # =================================================
    # CONTROLS
    # =================================================
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("▶ Start / Generate"):
            st.session_state.manual_running = True

    with c2:
        if st.button("⏸ Pause"):
            st.session_state.manual_running = False

    with c3:
        if st.button("⏹ Reset"):
            st.session_state.manual_running = False
            st.session_state.manual_global_time_us = 0.0
            st.session_state.manual_pdw_buffer = []

    # =================================================
    # GENERATE PDWs
    # =================================================
    if st.session_state.manual_running:

        rows = []

        window_start = st.session_state.manual_global_time_us
        window_end = window_start + 2e6
        st.session_state.manual_global_time_us = window_end

        for e in emitters:

            toa = np.random.uniform(window_start, window_end)

            for k in range(pulses_per_emitter):

                freq = e["freqs"][k % len(e["freqs"])]
                pri  = e["pri_values"][k % len(e["pri_values"])]

                if e["pri_type"] == "Jittered":
                    pri = pri + np.random.normal(0, 0.02 * pri)

                rows.append({
                    "freq_MHz": freq + np.random.normal(0, 5),
                    "pri_us": pri,
                    "pw_us": e["pw"] + np.random.normal(0, 0.05 * e["pw"]),
                    "doa_deg": e["doa"] + np.random.normal(0, 2),
                    "amp_dB": e["amp"] + np.random.normal(0, 1),
                    "toa_us": toa
                })

                toa += pri
                if toa > window_end:
                    break

        out_dir = st.session_state.get("user_output_dir", OUTPUT_DIR)
        st.session_state.manual_pdw_buffer.extend(rows)


        df_all = pd.DataFrame(st.session_state.manual_pdw_buffer)

        df_all = df_all.sort_values("toa_us").round(2)
        df_all["toa_hms"] = df_all["toa_us"].apply(toa_us_to_hms)
        df_all.to_csv(f"{out_dir}/manual_interleaved.csv", index=False)

        st.session_state.manual_running = False
        st.success(f"Generated 2 seconds of PDWs (Total: {len(df_all)})")
        st.dataframe(df_all.tail(20))
