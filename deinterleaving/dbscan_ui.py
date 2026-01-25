import streamlit as st
import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN, KMeans
import matplotlib.pyplot as plt
from reports.report_gen import generate_pdf_report

# Try importing HDBSCAN
try:
    from sklearn.cluster import HDBSCAN
    HAS_HDBSCAN = True
    HDBSCAN_LIB = "sklearn"
except ImportError:
    try:
        import hdbscan
        HAS_HDBSCAN = True
        HDBSCAN_LIB = "hdbscan"
    except ImportError:
        HAS_HDBSCAN = False
        HDBSCAN_LIB = None


def dbscan_ui():

    state = st.session_state.dbscan_state

    st.header("De-Interleaving Phase")

    st.info(
        "Live PDW De-Interleaving using density-based clustering "
        "(DBSCAN / HDBSCAN)."
    )

    # =================================================
    # DATA SOURCE
    # =================================================
    # =================================================
    # DATA SOURCE
    # =================================================
    last_mode = st.session_state.get("last_active_mode", "Auto")
    default_idx = 0 if last_mode == "Auto" else 1
    
    # Load persisted index if available, else usage default
    saved_ds_idx = state.get("data_source_idx", default_idx)
    
    data_source_opts = ["Auto Mode (Live)", "Manual Mode (Live)"]
    if saved_ds_idx >= len(data_source_opts): saved_ds_idx = 0

    data_source = st.radio(
        "Data Source",
        data_source_opts,
        index=saved_ds_idx,
        horizontal=True
    )
    # Save selection
    state["data_source_idx"] = data_source_opts.index(data_source)

    df_input = None
    known_emitters = None

    if data_source == "Auto Mode (Live)":
        if st.button("Load / Refresh Auto Mode Data"):
            buf = st.session_state.get("pdw_buffer", [])
            if not buf:
                st.warning("Auto Mode buffer is empty.")
            else:
                state["df"] = pd.DataFrame(buf)
                state["results"] = None
                state["summary"] = None
                state.pop("tuned_params_dbscan", None)

        df_input = state.get("df")
        known_emitters = st.session_state.get("auto_config", {}).get("num_emitters")

    elif data_source == "Manual Mode (Live)":
        if st.button("Load / Refresh Manual Mode Data"):
            buf = st.session_state.get("manual_pdw_buffer", [])
            if not buf:
                st.warning("Manual Mode buffer is empty.")
            else:
                state["df"] = pd.DataFrame(buf)
                state["results"] = None
                state["summary"] = None
                state.pop("tuned_params_dbscan", None)

        df_input = state.get("df")
        known_emitters = st.session_state.get("manual_config", {}).get("num_emitters")

    if df_input is None:
        return

    st.subheader("Input PDW Data")
    st.caption(f"Total PDWs: {len(df_input)}")
    if known_emitters:
        st.success(f"Ground Truth Emitters: {known_emitters}")
    st.dataframe(df_input.head(10))
    st.divider()

    # =================================================
    # FEATURE SELECTION
    # =================================================
    st.subheader("Feature Selection")

    saved_feats = state.get("features", ["freq_MHz", "pri_us"])

    c1, c2, c3, c4 = st.columns(4)
    use_freq = c1.checkbox("Frequency", value="freq_MHz" in saved_feats)
    use_pri  = c2.checkbox("PRI", value="pri_us" in saved_feats)
    use_pw   = c3.checkbox("PW", value="pw_us" in saved_feats)
    use_doa  = c4.checkbox("DOA", value="doa_deg" in saved_feats)

    features = []
    if use_freq: features.append("freq_MHz")
    if use_pri:  features.append("pri_us")
    if use_pw and "pw_us" in df_input.columns: features.append("pw_us")
    if use_doa and "doa_deg" in df_input.columns: features.append("doa_deg")

    state["features"] = features

    if not features:
        st.error("Select at least one feature.")
        return

    st.divider()

    # =================================================
    # ALGORITHM SELECTION
    # =================================================
    algo_options = ["DBSCAN"]
    if HAS_HDBSCAN:
        algo_options.append("HDBSCAN")
    algo_options.append("K-Means")

    # Load persisted algo index
    saved_algo_idx = state.get("algo_idx", 0)
    if saved_algo_idx >= len(algo_options): saved_algo_idx = 0

    algorithm = st.selectbox("Clustering Algorithm", algo_options, index=saved_algo_idx)
    state["algo_idx"] = algo_options.index(algorithm)

    params = {}

    # =================================================
    # DBSCAN PARAMS (AUTO-TUNED / MANUAL)
    # =================================================
    if algorithm == "DBSCAN":

        if known_emitters and "tuned_params_dbscan" not in state:
            with st.spinner("Auto-tuning DBSCAN…"):
                best_err = float("inf")
                best_eps = 0.5
                best_ms = 5

                X = StandardScaler().fit_transform(df_input[features].values)

                for eps in np.arange(0.1, 3.0, 0.1):
                    db = DBSCAN(eps=eps, min_samples=5)
                    labels = db.fit_predict(X)
                    clusters = len(set(labels)) - (1 if -1 in labels else 0)
                    err = abs(clusters - known_emitters)
                    if err < best_err:
                        best_err = err
                        best_eps = eps
                        best_ms = 5
                    if err == 0:
                        break

                state["tuned_params_dbscan"] = {
                    "eps": float(best_eps),
                    "min_samples": best_ms
                }

            st.success(f"Auto-Tuned DBSCAN → eps={best_eps:.2f}")

            st.success(f"Auto-Tuned DBSCAN → eps={best_eps:.2f}")

        # -----------------------------
        # -----------------------------
        # PARAMETER-SPECIFIC TOLERANCES
        # -----------------------------
        st.subheader("Clustering Tolerances (PDW Units)")
        
        # Default Tolerances (can be tuned)
        c1, c2 = st.columns(2)
        with c1:
            tol_freq = st.number_input("Freq Tolerance (±MHz)", 0.1, 100.0, 10.0, help="Max deviation: ±10 MHz")
            tol_pw   = st.number_input("PW Tolerance (±µs)", 0.01, 50.0, 2.0, help="Max deviation: ±2 µs")
        with c2:
            tol_pri  = st.number_input("PRI Tolerance (±µs)", 0.1, 500.0, 20.0, help="Max deviation: ±20 µs")
            tol_doa  = st.number_input("DOA Tolerance (±deg)", 0.1, 45.0, 5.0, help="Max deviation: ±5 deg")

        st.caption("These values define the 'Unit Distance' for the clustering algorithm.")

        # Global 'Tightness' multiplier (effectively Epsilon)
        # If set to 1.0, it respects the above tolerances exactly as the radius.
        eps_mult = st.slider("Cluster Tightness (Multiplier)", 0.1, 2.0, 1.0, 0.1, help="1.0 = Strict Tolerance. Higher = Looser clusters.")
        
        min_samples_val = st.slider("Min Pulses per Cluster", 2, 20, 5, 1)

        params["eps"] = eps_mult
        params["min_samples"] = min_samples_val
        
        # Store tolerances for processing
        st.session_state.custom_tols = {
            "freq_MHz": tol_freq,
            "pri_us": tol_pri,
            "pw_us": tol_pw,
            "doa_deg": tol_doa
        }

    # =================================================
    # HDBSCAN PARAMS
    # =================================================
    elif algorithm == "HDBSCAN":
        saved_min_cluster = state.get("hdbscan_min_cluster", 5)
        params["min_cluster_size"] = st.slider("Min Cluster Size", 2, 50, saved_min_cluster)
        state["hdbscan_min_cluster"] = params["min_cluster_size"]

        saved_min_samples = state.get("hdbscan_min_samples", 5)
        params["min_samples"] = st.slider("Min Samples", 1, 50, saved_min_samples)
        state["hdbscan_min_samples"] = params["min_samples"]

    # =================================================
    # K-MEANS PARAMS
    # =================================================
    elif algorithm == "K-Means":
        # Default to known emitters if available, else 3
        default_k = known_emitters if known_emitters else 3
        
        n_clusters = st.slider("Number of Clusters (K)", 2, 20, default_k)
        params["n_clusters"] = n_clusters

    # =================================================
    # RUN DE-INTERLEAVING
    # =================================================
    if st.button(f"Run {algorithm}"):

        if algorithm == "DBSCAN":
            # Apply Custom Scaling based on Tolerances
            # Formula: Value / Tolerance. 
            # Then Epsilon=1 (or user mult) means distance is normalized to tolerance.
            
            X_custom = df_input[features].copy()
            tols = st.session_state.get("custom_tols", {})
            
            for col in features:
                if col in tols:
                     X_custom[col] = X_custom[col] / tols[col]
            
            # Use the custom scaled X, not standard scaler
            # We must convert to values, handle NaNs if any (though shouldn't be)
            X_final = X_custom.fillna(0).values
            labels = DBSCAN(**params).fit_predict(X_final)

        elif algorithm == "HDBSCAN":
            # HDBSCAN still uses standard scaling for now
            X = StandardScaler().fit_transform(df_input[features].values)
            
            if HDBSCAN_LIB == "sklearn":
                labels = HDBSCAN(**params).fit_predict(X)
            else:
                labels = hdbscan.HDBSCAN(**params).fit_predict(X)

        elif algorithm == "K-Means":
            # K-Means uses standard scaling
            X = StandardScaler().fit_transform(df_input[features].values)
            labels = KMeans(**params, random_state=42, n_init=10).fit_predict(X)

        unique = sorted(set(labels))
        label_map = {l: i + 1 for i, l in enumerate(unique) if l != -1}
        label_map[-1] = 0

        mapped = [label_map[l] for l in labels]

        state["results"] = mapped
        state["summary"] = {
            "clusters": len(set(mapped)) - (1 if 0 in mapped else 0),
            "noise": mapped.count(0),
            "expected": known_emitters
        }

        st.success("De-Interleaving Completed")

    # =================================================
    # RESULTS DISPLAY – TABLE-ONLY, 3-WINDOW VIEW ✅ REPLACED
    # =================================================


    if state.get("results") is not None:

        df_out = df_input.copy()
        df_out["Emitter_ID"] = state["results"]

        summ = state["summary"]

        st.markdown(
            f"""
            ### ✅ De-Interleaving Summary
            - **Detected Emitters:** {summ['clusters']}
            - **Expected Emitters:** {summ.get('expected', 'Unknown')}
            - **Unassigned Pulses:** {summ['noise']}
            
            **Applied Tolerances:**
            - Freq: `±{st.session_state.custom_tols.get('freq_MHz', 'N/A')} MHz` | PRI: `±{st.session_state.custom_tols.get('pri_us', 'N/A')} µs`
            - Epsilon Mult: `{params.get('eps', 'N/A')}` | Min Samples: `{params.get('min_samples', 'N/A')}`
            """
        )

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
            st.markdown("### 🔀 Interleaved PDWs (Raw Input)")
            df_interleaved = df_input.sort_values("toa_us").round(2)
            
            # Hide raw toa_us if preferred, or keep both. 
            # Reordering to show Time first.
            cols = ["freq_MHz", "pri_us", "pw_us", "doa_deg", "amp_dB"]
            st.dataframe(df_interleaved[cols], height=420, use_container_width=True)
            st.caption("Raw interleaved PDW stream")

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
            st.caption("Emitter-wise de-interleaving result")

        # WINDOW 3 — EMITTER TRACKING
        with col3:
            st.markdown("### 📡 Emitter Tracking")
            emitter_ids = df_emitters["Emitter_ID"].tolist()

            if not emitter_ids:
                st.warning("No emitters detected.")
            else:
                saved_emitter_idx = state.get("selected_emitter_idx", 0)
                if saved_emitter_idx >= len(emitter_ids): saved_emitter_idx = 0
                
                selected_emitter = st.selectbox("Select Emitter ID", emitter_ids, index=saved_emitter_idx)
                state["selected_emitter_idx"] = emitter_ids.index(selected_emitter)
                df_track = (
                    df_out[df_out["Emitter_ID"] == selected_emitter]
                    .sort_values("toa_us")
                    .round(2)
                )

                st.write(
                    f"**Emitter {selected_emitter} — Pulses: {len(df_track)}**"
                )

                st.dataframe(
                    df_track[
                        ["freq_MHz", "pri_us", "pw_us", "doa_deg", "amp_dB"]
                    ],
                    height=360,
                    use_container_width=True
                )

        # SAVE OUTPUT
        out_dir = st.session_state.get("user_output_dir", "outputs")
        df_out.round(2).to_csv(
            f"{out_dir}/deinterleaved_pdws.csv",
            index=False
        )

        st.success("De-interleaved PDWs saved successfully.")
