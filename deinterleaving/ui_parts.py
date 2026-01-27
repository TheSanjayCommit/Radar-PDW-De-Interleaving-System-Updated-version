import streamlit as st
import pandas as pd
import numpy as np
from deinterleaving.logic import HAS_HDBSCAN
from reports.report_gen import generate_pdf_report

def render_settings(state_key_prefix="auto", known_emitters=None):
    """
    Renders the De-Interleaving settings (Algo, Tolerances) and returns the configuration.
    """
    st.subheader("De-Interleaving Configuration")
    
    with st.expander("Algorithm & Tolerances", expanded=True):
        
        # 1. Feature Selection
        # st.caption("Feature Selection")
        # Defaults
        saved_feats = st.session_state.get(f"{state_key_prefix}_features", ["freq_MHz", "pri_us"])
        
        c1, c2, c3, c4 = st.columns(4)
        use_freq = c1.checkbox("Frequency", value="freq_MHz" in saved_feats, key=f"{state_key_prefix}_use_freq")
        use_pri  = c2.checkbox("PRI", value="pri_us" in saved_feats, key=f"{state_key_prefix}_use_pri")
        use_pw   = c3.checkbox("PW", value="pw_us" in saved_feats, key=f"{state_key_prefix}_use_pw")
        use_doa  = c4.checkbox("DOA", value="doa_deg" in saved_feats, key=f"{state_key_prefix}_use_doa")

        features = []
        if use_freq: features.append("freq_MHz")
        if use_pri:  features.append("pri_us")
        if use_pw:   features.append("pw_us") # Assumes column existence check done before execution
        if use_doa:  features.append("doa_deg")
        
        st.session_state[f"{state_key_prefix}_features"] = features

        st.divider()

        # 2. Algo Selection
        algo_options = ["DBSCAN"]
        if HAS_HDBSCAN:
            algo_options.append("HDBSCAN")
        algo_options.append("K-Means")

        saved_algo_idx = st.session_state.get(f"{state_key_prefix}_algo_idx", 0)
        if saved_algo_idx >= len(algo_options): saved_algo_idx = 0

        algorithm = st.selectbox("Clustering Algorithm", algo_options, index=saved_algo_idx, key=f"{state_key_prefix}_algo_select")
        st.session_state[f"{state_key_prefix}_algo_idx"] = algo_options.index(algorithm)

        params = {}
        custom_tols = {}

        # 3. Parameters
        if algorithm == "DBSCAN":
            st.caption("Clustering Tolerances (PDW Units)")
            c1, c2 = st.columns(2)
            with c1:
                tol_freq = st.number_input("Freq Tolerance (±MHz)", 0.1, 100.0, 10.0, key=f"{state_key_prefix}_tol_freq")
                tol_pw   = st.number_input("PW Tolerance (±µs)", 0.01, 50.0, 2.0, key=f"{state_key_prefix}_tol_pw")
            with c2:
                tol_pri  = st.number_input("PRI Tolerance (±µs)", 0.1, 500.0, 20.0, key=f"{state_key_prefix}_tol_pri")
                tol_doa  = st.number_input("DOA Tolerance (±deg)", 0.1, 45.0, 5.0, key=f"{state_key_prefix}_tol_doa")

            custom_tols = {
                "freq_MHz": tol_freq,
                "pri_us": tol_pri,
                "pw_us": tol_pw,
                "doa_deg": tol_doa
            }

            eps_mult = st.slider("Cluster Tightness (Multiplier)", 0.1, 2.0, 1.0, 0.1, key=f"{state_key_prefix}_eps")
            min_samples = st.slider("Min Pulses per Cluster", 2, 20, 5, 1, key=f"{state_key_prefix}_min_samples")
            
            params["eps"] = eps_mult
            params["min_samples"] = min_samples

        elif algorithm == "HDBSCAN":
            min_cluster = st.slider("Min Cluster Size", 2, 50, 5, key=f"{state_key_prefix}_h_min_cluster")
            min_samples = st.slider("Min Samples", 1, 50, 5, key=f"{state_key_prefix}_h_min_samples")
            params["min_cluster_size"] = min_cluster
            params["min_samples"] = min_samples
            
        elif algorithm == "K-Means":
            default_k = known_emitters if known_emitters else 3
            n_clusters = st.slider("Number of Clusters (K)", 2, 20, default_k, key=f"{state_key_prefix}_k_clusters")
            params["n_clusters"] = n_clusters

        return {
            "algorithm": algorithm,
            "features": features,
            "params": params,
            "custom_tols": custom_tols
        }

def render_results(df_input, labels, summary, custom_tols, params):
    """
    Renders the results dashboard (tables and PDF download).
    """
    if df_input is None or labels is None:
        return

    df_out = df_input.copy()
    df_out["Emitter_ID"] = labels

    summ = summary
    
    st.success("De-Interleaving Completed")

    st.markdown(
        f"""
        ### ✅ De-Interleaving Summary
        - **Detected Emitters:** {summ['clusters']}
        - **Expected Emitters:** {summ.get('expected', 'Unknown')}
        - **Unassigned Pulses:** {summ['noise']}
        """
    )
    # Display tolerances if available
    if custom_tols:
        st.caption(f"Freq Tol: ±{custom_tols.get('freq_MHz')} MHz | PRI Tol: ±{custom_tols.get('pri_us')} µs")

    st.caption("Download Report")
    pdf_bytes = generate_pdf_report(df_out, summ)
    st.download_button(
        label="📄 Download Mission Report (PDF)",
        data=pdf_bytes,
        file_name="mission_report.pdf",
        mime="application/pdf"
    )

    st.divider()
    st.subheader("📊 PDW De-Interleaving View")

    col1, col2, col3 = st.columns([1.3, 1.1, 1.2])

    # WINDOW 1 — INTERLEAVED PDWs
    with col1:
        st.markdown("### 🔀 Interleaved PDWs")
        df_interleaved = df_input.sort_values("toa_us").round(2)
        cols = ["freq_MHz", "pri_us", "pw_us", "doa_deg", "amp_dB"]
        st.dataframe(df_interleaved[cols], height=420, use_container_width=True)

    # WINDOW 2 — DE-INTERLEAVED EMITTER SUMMARY
    with col2:
        st.markdown("### 🎯 Detected Emitters")
        df_emitters = (
            df_out[df_out["Emitter_ID"] != 0]
            .groupby("Emitter_ID")
            .agg(
                Pulses=("Emitter_ID", "count"),
                Mean_Freq_MHz=("freq_MHz", "mean"),
                Mean_PRI_us=("pri_us", "mean")
            )
            .round(2)
            .reset_index()
        )
        st.dataframe(df_emitters, height=420, use_container_width=True)

    # WINDOW 3 — EMITTER TRACKING
    with col3:
        st.markdown("### 📡 Emitter Tracking")
        emitter_ids = df_emitters["Emitter_ID"].tolist()

        if not emitter_ids:
            st.warning("No emitters detected.")
        else:
            selected_emitter = st.selectbox("Select Emitter ID", emitter_ids)
            df_track = (
                df_out[df_out["Emitter_ID"] == selected_emitter]
                .sort_values("toa_us")
                .round(2)
            )
            st.write(f"**Emitter {selected_emitter} — Pulses: {len(df_track)}**")
            st.dataframe(
                df_track[["freq_MHz", "pri_us", "pw_us", "doa_deg", "amp_dB"]],
                height=360,
                use_container_width=True
            )
