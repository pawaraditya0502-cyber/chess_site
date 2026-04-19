import streamlit as st
import hashlib
import json
import os

st.set_page_config(page_title="Chess Academy — Login", page_icon="♚", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Lato:wght@300;400;700&display=swap');
html,body,[class*="css"]{font-family:'Lato',sans-serif;background-color:#0a0a0a;color:#ede8df}
.main{background-color:#0a0a0a}
.block-container{padding:3rem 2rem;max-width:480px}
h1,h2,h3{font-family:'Cinzel',serif!important;color:#ede8df!important}

.hero-box{
    background:linear-gradient(135deg,#111,#1a1a1a);
    border-left:4px solid #c9922e;
    border:1px solid rgba(255,255,255,0.07);
    padding:2rem 1.8rem;border-radius:6px;
    margin-bottom:2rem;text-align:center
}
.hero-title{font-family:'Cinzel',serif;font-size:2rem;color:#e8b84b}
.hero-sub{color:rgba(237,232,223,0.5);font-size:0.85rem;margin-top:0.4rem}

.form-box{
    background:#111;
    border:1px solid rgba(255,255,255,0.07);
    border-radius:8px;
    padding:2rem 1.8rem;
    margin-bottom:1rem;
}
.form-title{
    font-family:'Cinzel',serif;
    font-size:1.3rem;color:#e8b84b;
    margin-bottom:1.2rem;text-align:center
}
.gold-line{border:none;border-top:1px solid rgba(201,146,46,0.2);margin:1.2rem 0}
.success-box{
    background:rgba(42,122,96,0.15);
    border:1px solid rgba(42,122,96,0.4);
    border-radius:6px;padding:1rem;
    color:#3db890;font-size:0.9rem;
    text-align:center;margin-bottom:1rem
}
.error-box{
    background:rgba(184,56,32,0.15);
    border:1px solid rgba(184,56,32,0.4);
    border-radius:6px;padding:1rem;
    color:#e07050;font-size:0.9rem;
    text-align:center;margin-bottom:1rem
}
.welcome-box{
    background:linear-gradient(135deg,#111,#181818);
    border:1px solid rgba(255,255,255,0.07);
    border-left:4px solid #c9922e;
    border-radius:6px;padding:2rem;
    text-align:center;margin-bottom:1.5rem
}
.welcome-title{
    font-family:'Cinzel',serif;
    font-size:1.8rem;color:#e8b84b;margin-bottom:0.5rem
}
.welcome-sub{color:rgba(237,232,223,0.6);font-size:0.9rem}

/* Input fields */
div[data-testid="stTextInput"] input{
    background:#1a1a1a!important;
    border:1px solid rgba(255,255,255,0.12)!important;
    border-radius:4px!important;
    color:#ede8df!important;
    padding:0.6rem 1rem!important;
}
div[data-testid="stTextInput"] input:focus{
    border-color:#c9922e!important;
}

/* Buttons */
div[data-testid="stButton"] button{
    background:#c9922e!important;
    color:#0a0a0a!important;
    border:none!important;
    font-weight:700!important;
    border-radius:4px!important;
    width:100%!important;
    padding:0.6rem!important;
    font-size:0.9rem!important;
    letter-spacing:0.05em!important;
}
div[data-testid="stButton"] button:hover{background:#e8b84b!important}
</style>
""", unsafe_allow_html=True)

# ── User Storage (JSON file) ──────────────────────────────────────────────────
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, email):
    users = load_users()
    if username in users:
        return False, "Username already exists!"
    if len(username) < 3:
        return False, "Username must be at least 3 characters!"
    if len(password) < 6:
        return False, "Password must be at least 6 characters!"
    if "@" not in email:
        return False, "Please enter a valid email!"
    users[username] = {
        "password": hash_password(password),
        "email": email,
    }
    save_users(users)
    return True, "Account created successfully!"

def login_user(username, password):
    users = load_users()
    if username not in users:
        return False, "Username not found!"
    if users[username]["password"] != hash_password(password):
        return False, "Wrong password!"
    return True, "Login successful!"

# ── Session State ─────────────────────────────────────────────────────────────
if "logged_in"  not in st.session_state: st.session_state.logged_in  = False
if "username"   not in st.session_state: st.session_state.username   = ""
if "auth_mode"  not in st.session_state: st.session_state.auth_mode  = "login"

# ── LOGGED IN VIEW ────────────────────────────────────────────────────────────
if st.session_state.logged_in:
    st.markdown(f"""
    <div class='welcome-box'>
        <div style='font-size:3rem'>♚</div>
        <div class='welcome-title'>Welcome, {st.session_state.username}!</div>
        <div class='welcome-sub'>You are signed in to Chess Academy</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#111;border:1px solid rgba(255,255,255,0.07);
                border-radius:8px;padding:1.5rem;margin-bottom:1rem'>
        <div style='font-family:Cinzel,serif;color:#e8b84b;font-size:1rem;margin-bottom:1rem'>
            🎓 Your Chess Academy
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style='background:#111;border:1px solid rgba(255,255,255,0.07);
                    border-radius:8px;padding:1.2rem;text-align:center'>
            <div style='font-size:2rem'>♟</div>
            <div style='font-family:Cinzel,serif;color:#e8b84b;font-size:0.95rem;margin:0.4rem 0'>Chess Lessons</div>
            <div style='color:rgba(237,232,223,0.5);font-size:0.78rem'>Learn openings, middlegame & endgame</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style='background:#111;border:1px solid rgba(255,255,255,0.07);
                    border-radius:8px;padding:1.2rem;text-align:center'>
            <div style='font-size:2rem'>🎬</div>
            <div style='font-family:Cinzel,serif;color:#e8b84b;font-size:0.95rem;margin:0.4rem 0'>Video Lessons</div>
            <div style='color:rgba(237,232,223,0.5);font-size:0.78rem'>GothamChess & Igor Smirnov</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)

    if st.button("🚪 Sign Out"):
        st.session_state.logged_in = False
        st.session_state.username  = ""
        st.rerun()

# ── NOT LOGGED IN VIEW ────────────────────────────────────────────────────────
else:
    # Hero
    st.markdown("""
    <div class='hero-box'>
        <div class='hero-title'>♚ Chess Academy</div>
        <div style='color:#c9922e;font-size:0.72rem;letter-spacing:0.2em;
                    text-transform:uppercase;margin:0.4rem 0'>Sign In to Continue</div>
        <div class='hero-sub'>Learn openings, middlegame, endgame & watch video lessons</div>
    </div>
    """, unsafe_allow_html=True)

    # Toggle Login / Sign Up
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔑 Sign In", key="toggle_login"):
            st.session_state.auth_mode = "login"
            st.rerun()
    with col2:
        if st.button("📝 Sign Up", key="toggle_signup"):
            st.session_state.auth_mode = "signup"
            st.rerun()

    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)

    # ── LOGIN FORM ────────────────────────────────────────────────────────────
    if st.session_state.auth_mode == "login":
        st.markdown("<div class='form-title'>🔑 Sign In</div>", unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter your username", key="login_user")
        password = st.text_input("Password", placeholder="Enter your password", type="password", key="login_pass")

        st.markdown("")

        if st.button("Sign In →"):
            if not username or not password:
                st.markdown("<div class='error-box'>⚠ Please fill in all fields!</div>", unsafe_allow_html=True)
            else:
                success, message = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username  = username
                    st.markdown(f"<div class='success-box'>✅ {message}</div>", unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.markdown(f"<div class='error-box'>❌ {message}</div>", unsafe_allow_html=True)

        st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;color:rgba(237,232,223,0.4);font-size:0.82rem'>Don't have an account? Tap Sign Up above</div>", unsafe_allow_html=True)

    # ── SIGNUP FORM ───────────────────────────────────────────────────────────
    else:
        st.markdown("<div class='form-title'>📝 Create Account</div>", unsafe_allow_html=True)

        new_username = st.text_input("Username",         placeholder="Choose a username",  key="reg_user")
        new_email    = st.text_input("Email",            placeholder="Enter your email",    key="reg_email")
        new_password = st.text_input("Password",         placeholder="Choose a password (min 6 chars)", type="password", key="reg_pass")
        confirm_pass = st.text_input("Confirm Password", placeholder="Repeat your password", type="password", key="reg_confirm")

        st.markdown("")

        if st.button("Create Account →"):
            if not new_username or not new_email or not new_password or not confirm_pass:
                st.markdown("<div class='error-box'>⚠ Please fill in all fields!</div>", unsafe_allow_html=True)
            elif new_password != confirm_pass:
                st.markdown("<div class='error-box'>❌ Passwords do not match!</div>", unsafe_allow_html=True)
            else:
                success, message = register_user(new_username, new_password, new_email)
                if success:
                    st.markdown(f"<div class='success-box'>✅ {message} Please sign in now.</div>", unsafe_allow_html=True)
                    st.session_state.auth_mode = "login"
                    st.rerun()
                else:
                    st.markdown(f"<div class='error-box'>❌ {message}</div>", unsafe_allow_html=True)

        st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;color:rgba(237,232,223,0.4);font-size:0.82rem'>Already have an account? Tap Sign In above</div>", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:rgba(237,232,223,0.2);font-size:0.72rem'>♚ Chess Academy — Your Chess Learning Journey</div>", unsafe_allow_html=True)
