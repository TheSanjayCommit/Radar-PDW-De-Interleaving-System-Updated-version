# Radar PDW De-Interleaving System (Secure Offline)

A comprehensive Electronic Warfare (EW) simulation and analysis tool designed to generate, visualize, and de-interleave Radar Pulse Descriptor Words (PDWs). The system features a secure, multi-user environment with strict Admin Gatekeeper access.

## 🚀 Key Features

### 1. 🔐 Enhanced Security (Gatekeeper Model)
*   **3-Stage Authentication Flow**:
    1.  **System Lock**: The application starts in a locked state. Only an **Admin** can unlock it.
    2.  **User Access**: Once unlocked, Users can **Sign In** (Existing) or **Register** (New).
    3.  **Dashboard**: Secure, private workspace for the authenticated session.
*   **Role-Based Access**: Admins have a dedicated dashboard to view registered users.
*   **Credentials**:
    *   **Admin**: `Dharashakti@123` / `123456789`
*   **Encryption**: All passwords are securely **Salted & Hashed (SHA-256)**.

### 2. ⚡ PDW Simulation
*   **Auto Mode**:
    *   Generates complex interleaved pulse streams automatically.
    *   Configurable **Emitter Count** (1-10) and duration.
    *   Simulates realistic attributes: Frequency, PRI (Pulse Repetition Interval), Pulse Width, DOA (Direction of Arrival).
*   **Manual Mode**:
    *   Detailed control over every emitter.
    *   **Frequency Agility**: Define multiple frequency modes or hoping patterns.
    *   **Staggered PRI**: Define complex PRI sequences.
    *   Interactive "Start/Pause/Reset" controls for continuous time simulation.

### 3. 🧠 De-Interleaving & Analysis
A powerful module to separate interleaved pulses back into distinct emitters.
*   **Live Data Link**: Seamlessly loads data from the active Simulation buffer (Auto or Manual).
*   **Algorithm Suite**:
    *   **K-Means**: The "Ground Truth" solver. If the number of emitters is known (Live Mode), this guarantees **Exact Clustering**.
    *   **HDBSCAN**: Robust, hierarchical density-based clustering. Features **✨ Auto-Tune** which automatically scans parameters to match the expected emitter count.
    *   **DBSCAN**: Standard density clustering. Also updated with **Auto-Tune** logic for optimizing `Epsilon`.
*   **Analysis**:
    *   Calculates statistics per cluster (Mean Freq, PRI, Std Dev).
    *   Interactive Scatter Plots (TOA vs Frequency).
    *   Pulse Consistency checks.

### 4. 📂 Data Management
*   **Per-User Isolation**: Every user gets a private workspace (`outputs/username/`). Data is never shared between users.
*   **History**: "My Files" tab allows users to view their generated datasets.

---

## 🛠️ Algorithms Explained

### K-Means Clustering
*   **Type**: Partitioning.
*   **Use Case**: When the **Number of Emitters (k)** is known exactly (e.g., Live Simulation).
*   **Mechanism**: Partitions $n$ pulses into $k$ clusters by minimizing the variance within each cluster.
*   **Advantage**: Extremely fast and forces an exact match to the simulation ground truth.

### HDBSCAN (Hierarchical DBSCAN)
*   **Type**: Density-based (Hierarchical).
*   **Use Case**: Complex environments with varying density; does not need a pre-set 'k'.
*   **Mechanism**: Builds a hierarchy of connected components and extracts the most stable clusters.
*   **Auto-Tune**: Our custom implementation checks the `known_emitters` count from the simulation and iteratively tests `min_cluster_size` (range 2-40) to find the configuration that yields the correct number of emitters.

### DBSCAN (Density-Based Spatial Clustering)
*   **Type**: Density-based.
*   **Use Case**: Finding arbitrary shaped clusters and filtering noise.
*   **Mechanism**: Groups points that are closely packed together (points with many nearby neighbors). Outliers are marked as Noise (-1).
*   **Auto-Tune**: Iteratively adjusts `Epsilon` ($\epsilon$) to find the spatial radius that separates the pulses into the correct number of groups.

---

## 💻 Installation & Usage

### Prerequisites
*   Python 3.8+
*   Packages: `streamlit`, `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `hdbscan` (optional, falls back to sklearn).

### Setup
1.  **Clone/Download** the repository.
2.  **Install Requirements**:
    ```bash
    pip install streamlit pandas numpy scikit-learn matplotlib hdbscan
    ```
3.  **Run Application**:
    ```bash
    streamlit run app.py
    ```

### Workflow
1.  **Unlock**: Enter Admin ID (`Dharashakti@123`) and Password (`123456789`).
2.  **User Entry**:
    *   **New?** Click "New User", enter Name, Email, Password.
    *   **Existing?** Click "Existing User", enter Email, Password.
3.  **Simulate**: Go to **Auto Mode**, select 5 Emitters, click **Start**.
4.  **Analyze**:
    *   Go to **De-Interleaving**.
    *   Select **Auto Mode (Live)**.
    *   Select Algorithm (e.g., **HDBSCAN**).
    *   Wait for **Auto-Tune** to finish.
    *   Click **Run HDBSCAN**.
5.  **Result**: Verify the "Detected Emitters" matches your simulation count.

---

## 📁 Project Structure

```
pdw_app/
├── app.py                 # Main Entry Point & Gatekeeper Logic
├── auth.py                # Secure Authentication Module (Salt/Hash)
├── users.csv              # Encrypted User Database
├── simulation/
│   ├── auto_mode.py       # Automated Simulation Logic
│   └── manual_mode.py     # Manual Control Logic
├── deinterleaving/
│   └── dbscan_ui.py       # Clustering Algorithms & Auto-Tune UI
└── outputs/
    └── {user_email}/      # Private User Data Folders
```

---
**Developed for Advanced Radar Signal Processing & EW Simulation.**
https://de-interleavingphase-5kaf5cg5xj4m2hr3cng8kr.streamlit.app/
