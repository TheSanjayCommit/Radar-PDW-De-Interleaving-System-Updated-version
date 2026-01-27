import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN, KMeans

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

def run_clustering(df, algo, params, features, custom_tols=None):
    """
    Runs the selected clustering algorithm on the provided DataFrame.
    
    Args:
        df: Input DataFrame
        algo: "DBSCAN", "HDBSCAN", or "K-Means"
        params: Dictionary of algorithm parameters
        features: List of feature columns to use
        custom_tols: Dictionary of tolerances for DBSCAN custom scaling
        
    Returns:
        labels: Array of cluster labels
    """
    
    if df is None or df.empty:
        return []

    # -----------------------
    # DBSCAN (Custom Scaling)
    # -----------------------
    if algo == "DBSCAN":
        # Apply Custom Scaling based on Tolerances
        # Formula: Value / Tolerance. 
        X_custom = df[features].copy()
        tols = custom_tols if custom_tols else {}
        
        for col in features:
            if col in tols:
                    X_custom[col] = X_custom[col] / tols[col]
        
        # Use the custom scaled X
        X_final = X_custom.fillna(0).values
        labels = DBSCAN(**params).fit_predict(X_final)

    # -----------------------
    # HDBSCAN
    # -----------------------
    elif algo == "HDBSCAN":
        X = StandardScaler().fit_transform(df[features].values)
        
        if HDBSCAN_LIB == "sklearn":
            labels = HDBSCAN(**params).fit_predict(X)
        elif HDBSCAN_LIB == "hdbscan":
            labels = hdbscan.HDBSCAN(**params).fit_predict(X)
        else:
            # Fallback if selected but not available (shouldn't happen via UI)
            labels = np.zeros(len(df))

    # -----------------------
    # K-MEANS
    # -----------------------
    elif algo == "K-Means":
        X = StandardScaler().fit_transform(df[features].values)
        labels = KMeans(**params, random_state=42, n_init=10).fit_predict(X)
        
    else:
        labels = np.zeros(len(df))

    return labels
