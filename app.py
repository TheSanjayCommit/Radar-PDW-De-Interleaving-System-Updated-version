import streamlit as st
import pandas as pd
import os
import auth

from simulation.auto_mode import auto_mode_ui
from simulation.manual_mode import manual_mode_ui
from deinterleaving.dbscan_ui import dbscan_ui

import streamlit as st
import pandas as pd
import os
import auth

from simulation.auto_mode import auto_mode_ui
from simulation.manual_mode import manual_mode_ui

# -------------------------------------------------
# APP CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Radar PDW System (Secure)", 
    layout="wide",
    initial_sidebar_state="collapsed" # Collapsed on login
)

# -------------------------------------------------
# SESSION STATE INIT
# -------------------------------------------------
# Stages:
# 1. admin_unlocked = False (Show Admin Login)
# 2. admin_unlocked = True, user_logged_in = False (Show User Login/Reg)
# 3. user_logged_in = True (Show Dashboard)

if "admin_unlocked" not in st.session_state: st.session_state.admin_unlocked = False
if "user_logged_in" not in st.session_state: st.session_state.user_logged_in = False

if "user_info" not in st.session_state: st.session_state.user_info = {}
if "auto_config" not in st.session_state: st.session_state.auto_config = {}
if "manual_config" not in st.session_state: st.session_state.manual_config = {}
if "dbscan_state" not in st.session_state:
    st.session_state.dbscan_state = {
        "df": None,
        "results": None,
        "features": ["freq_MHz", "pri_us"], 
        "summary": None
    }

# Ensure DB initialized
auth.init_db()

# -------------------------------------------------
# MAIN CONTROLLER
# -------------------------------------------------
def main():
    
    # STAGE 1: ADMIN GATEKEEPER
    if not st.session_state.admin_unlocked:
        admin_gatekeeper_ui()
        
    # STAGE 2: USER AUTHENTICATION
    elif not st.session_state.user_logged_in:
        user_auth_ui()
        
    # STAGE 3: APPLICATION DASHBOARD
    else:
        dashboard()

# -------------------------------------------------
# STAGE 1: ADMIN LOGIN
# -------------------------------------------------
def admin_gatekeeper_ui():
    st.markdown("<h1 style='text-align: center;'>🔐 System Locked</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Administrator Access Required</p>", unsafe_allow_html=True)
    
    st.divider()
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("admin_login_form"):
            u = st.text_input("Admin Login ID")
            p = st.text_input("Admin Password", type="password")
            submitted = st.form_submit_button("Unlock System", use_container_width=True)
            
            if submitted:
                # Check specific credentials as requested
                # Also verify against DB just in case, but user gave constants.
                # Let's verify using our auth module which now has this user.
                valid, user_data = auth.verify_user(u, p)
                
                if valid and user_data["role"] == "admin":
                    st.session_state.admin_unlocked = True
                    st.toast("✅ System Unlocked!", icon="🔓")
                    st.rerun()
                else:
                    st.error("❌ Access Denied: Invalid Admin Credentials")

# -------------------------------------------------
# STAGE 2: USER AUTH (New / Existing)
# -------------------------------------------------
def user_auth_ui():
    st.title("👤 User Access")
    
    choice = st.radio("Select Type", ["Existing User", "New User"], horizontal=True)
    
    st.divider()

    if choice == "Existing User":
        st.subheader("Login with Email")
        # Existing User: Mail ID and Password
        email = st.text_input("Email ID")
        pwd = st.text_input("Password", type="password")
        
        if st.button("Sign In"):
            valid, user_data = auth.verify_user(email, pwd)
            if valid:
                st.session_state.user_logged_in = True
                st.session_state.user_info = user_data.to_dict()
                st.toast(f"Welcome, {user_data['full_name']}!", icon="👋")
                st.rerun()
            else:
                st.error("❌ Invalid Email or Password")
                
    else: # NEW USER
        st.subheader("Register New Account")
        # New User: Name, Email, Password
        reg_name = st.text_input("Full Name")
        reg_email = st.text_input("Email ID")
        reg_pass = st.text_input("Password", type="password")
        
        if st.button("Register & Login"):
            if reg_name and reg_email and reg_pass:
                # Register
                ok, msg = auth.register_user(reg_name, reg_email, reg_pass, role="user")
                if ok:
                     st.toast("✅ Registration Successful!", icon="🎉")
                     # Auto Log in
                     valid, user_data = auth.verify_user(reg_email, reg_pass)
                     st.session_state.user_logged_in = True
                     st.session_state.user_info = user_data.to_dict()
                     st.rerun()
                else:
                    st.error(f"❌ {msg}")
            else:
                st.warning("Please fill all details.")

# -------------------------------------------------
# STAGE 3: MAIN DASHBOARD
# -------------------------------------------------
def dashboard():
    st.sidebar.title("Navigation")
    
    user = st.session_state.user_info
    
    # Define User's Private Output Directory
    # Ensure legal filename characters in email/username
    safe_uname = "".join([c if c.isalnum() else "_" for c in user['username']])
    user_out_dir = f"outputs/{safe_uname}"
    os.makedirs(user_out_dir, exist_ok=True)
    st.session_state.user_output_dir = user_out_dir

    # Sidebar Info
    st.sidebar.markdown(f"**👤 {user['full_name']}**")
    st.sidebar.caption(f"{user['email']}")
    
    if user['role'] == "admin":
        st.sidebar.success("Admin Mode")
        nav_options = ["Admin Panel", "Logout"]
    else:
        nav_options = ["Auto Mode", "Manual Mode", "De-Interleaving", "My Files", "Logout"]

    page = st.sidebar.radio("Go To", nav_options)

    # -----------------------------
    # PAGES
    # -----------------------------
    if page == "Admin Panel":
        st.title("🛠️ Admin Dashboard")
        st.write("### Registered System Users")
        users_df = auth.get_all_users()
        display_cols = ["username", "full_name", "email", "role"]
        st.dataframe(users_df[display_cols])

    elif page == "Auto Mode":
        auto_mode_ui()
        
    elif page == "Manual Mode":
        manual_mode_ui()

    elif page == "De-Interleaving":
        dbscan_ui()
    
    elif page == "My Files":
        st.title("📂 My Data History")
        st.write(f"Location: `{user_out_dir}`")
        files = os.listdir(user_out_dir)
        if files:
            files_df = pd.DataFrame(files, columns=["Filename"])
            st.dataframe(files_df)
        else:
            st.info("No generated files yet.")

    elif page == "Logout":
        logout_ui()

# -------------------------------------------------
# LOGOUT UI
# -------------------------------------------------
def logout_ui():
    st.warning("⚠️ **Log out and Lock System?**")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔒 Yes, Logout"):
            # Fully Reset
            st.session_state.user_logged_in = False
            st.session_state.admin_unlocked = False # LOCK SYSTEM
            st.session_state.user_info = {}
            st.toast("System Locked", icon="🔒")
            st.rerun()
    with c2:
        if st.button("Cancel"):
            st.rerun()

if __name__ == "__main__":
    main()
