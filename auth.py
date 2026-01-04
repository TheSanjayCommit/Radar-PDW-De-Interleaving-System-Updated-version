import pandas as pd
import hashlib
import os
import uuid
import re

USER_DB = "users.csv"

# -------------------------------------------------
# PASSWORD POLICY VALIDATION
# -------------------------------------------------
def validate_password(password: str):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong"

# -------------------------------------------------
# INITIALIZE DB
# -------------------------------------------------
def init_db():
    if not os.path.exists(USER_DB):
        df = pd.DataFrame(columns=[
            "username", "password", "salt",
            "full_name", "email", "role"
        ])

        # Create fixed admin account
        salt = uuid.uuid4().hex
        hashed_pw = hashlib.sha256((salt + "123456789").encode()).hexdigest()

        admin = pd.DataFrame([{
            "username": "Dharashakti@123",
            "password": hashed_pw,
            "salt": salt,
            "full_name": "System Administrator",
            "email": "admin@dharashakti.com",
            "role": "admin"
        }])

        df = pd.concat([df, admin], ignore_index=True)
        df.to_csv(USER_DB, index=False)

    else:
        df = pd.read_csv(USER_DB)
        if "Dharashakti@123" not in df["username"].values:
            salt = uuid.uuid4().hex
            hashed_pw = hashlib.sha256((salt + "123456789").encode()).hexdigest()
            admin = pd.DataFrame([{
                "username": "Dharashakti@123",
                "password": hashed_pw,
                "salt": salt,
                "full_name": "System Administrator",
                "email": "admin@dharashakti.com",
                "role": "admin"
            }])
            df = pd.concat([df, admin], ignore_index=True)
            df.to_csv(USER_DB, index=False)

# -------------------------------------------------
# VERIFY USER (LOGIN)
# -------------------------------------------------
def verify_user(identifier, password):
    init_db()
    df = pd.read_csv(USER_DB)

    user_row = df[
        (df["username"] == identifier) |
        (df["email"] == identifier)
    ]

    if user_row.empty:
        return False, None

    row = user_row.iloc[0]
    salt = row["salt"]
    stored_hash = row["password"]

    input_hash = hashlib.sha256((salt + password).encode()).hexdigest()

    if input_hash == stored_hash:
        return True, row

    return False, None

# -------------------------------------------------
# REGISTER USER (WITH PASSWORD RULES)
# -------------------------------------------------
def register_user(full_name, email, password, role="user"):
    init_db()
    df = pd.read_csv(USER_DB)

    if email in df["email"].values:
        return False, "Email already registered."

    # 🔐 PASSWORD VALIDATION HERE
    valid, msg = validate_password(password)
    if not valid:
        return False, msg

    salt = uuid.uuid4().hex
    hashed_pw = hashlib.sha256((salt + password).encode()).hexdigest()

    new_user = pd.DataFrame([{
        "username": email,
        "password": hashed_pw,
        "salt": salt,
        "full_name": full_name,
        "email": email,
        "role": role
    }])

    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USER_DB, index=False)

    # Create user workspace
    os.makedirs(f"outputs/{email}", exist_ok=True)

    return True, "Registration successful."

# -------------------------------------------------
# ADMIN VIEW
# -------------------------------------------------
def get_all_users():
    init_db()
    return pd.read_csv(USER_DB)
