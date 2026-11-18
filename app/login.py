import streamlit as st

from app import auth


def require_login() -> str:
    """Shows the sign-in screen until a role is chosen. Returns 'demo' or 'admin'."""
    role = st.session_state.get("role")
    if role:
        return role

    st.subheader("Sign in")
    st.write("Choose how you want to use the demo.")

    if st.button("Continue as demo user"):
        st.session_state["role"] = "demo"
        st.rerun()

    secret = auth.get_secret()
    if secret:
        st.divider()
        st.write("**Admin sign-in** (Google Authenticator)")
        with st.form("admin_login"):
            code = st.text_input("6-digit code", max_chars=7)
            submitted = st.form_submit_button("Sign in as admin")
        if submitted:
            if auth.is_locked():
                st.error("Too many failed attempts. Try again in a few minutes, or continue as demo user.")
            elif auth.verify_code(secret, code):
                st.session_state["role"] = "admin"
                st.rerun()
            else:
                st.error("That code is not valid. Check the code and your phone's clock.")
    st.stop()