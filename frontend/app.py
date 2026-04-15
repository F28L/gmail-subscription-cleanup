import streamlit as st
import requests
from datetime import datetime
from typing import Optional

from frontend.config import get_api_base_url
from frontend.components.subscription_card import (
    render_subscription_card,
    render_scan_controls,
)

API_BASE_URL = get_api_base_url()


def get_auth_status() -> dict:
    try:
        response = requests.get(f"{API_BASE_URL}/auth/status", timeout=5)
        return response.json()
    except Exception as e:
        return {"is_authenticated": False, "error": str(e)}


def get_auth_url() -> str:
    try:
        response = requests.get(f"{API_BASE_URL}/auth/url", timeout=5)
        return response.json().get("auth_url", "")
    except Exception as e:
        return ""


def get_subscriptions() -> list:
    try:
        response = requests.get(f"{API_BASE_URL}/subscriptions", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


def get_subscription_with_emails(subscription_id: str) -> Optional[dict]:
    try:
        response = requests.get(
            f"{API_BASE_URL}/subscriptions/{subscription_id}", timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def generate_description(subscription_id: str) -> Optional[str]:
    try:
        response = requests.post(
            f"{API_BASE_URL}/subscriptions/{subscription_id}/generate-description",
            json={"emails": []},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("description")
        return None
    except Exception:
        return None


def unsubscribe(subscription_id: str) -> bool:
    try:
        response = requests.post(
            f"{API_BASE_URL}/subscriptions/{subscription_id}/unsubscribe", timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


def scan_emails(days: int) -> dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}/scan", json={"days": days}, timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return {"error": "Scan failed"}
    except Exception as e:
        return {"error": str(e)}


def get_scan_status() -> dict:
    try:
        response = requests.get(f"{API_BASE_URL}/scan/status", timeout=5)
        return response.json()
    except Exception:
        return {"is_scanning": False, "subscriptions_found": 0}


def logout():
    try:
        requests.post(f"{API_BASE_URL}/auth/logout", timeout=5)
    except Exception:
        pass


def init_session_state():
    if "subscriptions" not in st.session_state:
        st.session_state.subscriptions = []

    if "marked_for_removal" not in st.session_state:
        st.session_state.marked_for_removal = set()

    if "scan_days" not in st.session_state:
        st.session_state.scan_days = 30

    if "refresh_trigger" not in st.session_state:
        st.session_state.refresh_trigger = 0


def main():
    st.set_page_config(
        page_title="Gmail Subscription Cleanup", page_icon="📧", layout="wide"
    )

    init_session_state()

    st.title("📧 Gmail Subscription Cleanup")

    auth_status = get_auth_status()

    if not auth_status.get("is_authenticated", False):
        st.warning("⚠️ Please authenticate with Gmail first")

        if st.button("🔐 Authenticate with Gmail"):
            auth_url = get_auth_url()
            if auth_url:
                import webbrowser

                webbrowser.open(auth_url)
                st.info(
                    "Please complete authentication in the browser, then refresh this page."
                )
            else:
                st.error("Could not get authentication URL. Is the backend running?")

        st.markdown("""
        ### Setup Instructions
        
        1. Make sure the backend is running: `uv run uvicorn backend.main:app --reload`
        2. Click 'Authenticate with Gmail' above
        3. Complete the OAuth flow in your browser
        4. Return here and refresh the page
        """)
        return

    st.success(f"✅ Authenticated as {auth_status.get('email', 'Unknown')}")

    with st.sidebar:
        st.markdown("### Account")
        if st.button("🚪 Logout"):
            logout()
            st.rerun()

        st.markdown("---")

        days_options = {"30 days": 30, "60 days": 60, "90 days": 90}
        scan_days = st.selectbox(
            "Scan period",
            options=list(days_options.keys()),
            index=list(days_options.keys()).index(f"{st.session_state.scan_days} days")
            if f"{st.session_state.scan_days} days" in days_options
            else 0,
            key="scan_days_select",
        )

        current_days = days_options.get(scan_days, 30)
        if current_days != st.session_state.scan_days:
            st.session_state.scan_days = current_days

        scan_status = get_scan_status()

        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "🔍 Scan",
                use_container_width=True,
                disabled=scan_status.get("is_scanning", False),
            ):
                with st.spinner("Scanning emails..."):
                    result = scan_emails(st.session_state.scan_days)
                    if "error" not in result:
                        st.session_state.subscriptions = get_subscriptions()
                        st.success(
                            f"Found {len(st.session_state.subscriptions)} subscriptions!"
                        )
                    else:
                        st.error(f"Scan failed: {result.get('error')}")
                st.rerun()

        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.session_state.subscriptions = get_subscriptions()
                st.rerun()

    scan_status = get_scan_status()
    st.markdown(
        f"**Status:** {'🔄 Scanning...' if scan_status.get('is_scanning') else '✅ Ready'} | "
        f"**Subscriptions:** {scan_status.get('subscriptions_found', 0)}"
    )

    st.markdown("---")

    if not st.session_state.subscriptions:
        st.info("👆 Click 'Scan' in the sidebar to find your subscriptions")
    else:
        subscriptions_with_details = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, sub in enumerate(st.session_state.subscriptions):
            status_text.text(
                f"Loading subscription {i + 1}/{len(st.session_state.subscriptions)}..."
            )
            progress_bar.progress((i + 1) / len(st.session_state.subscriptions))

            sub_with_emails = get_subscription_with_emails(sub.get("id", ""))
            if sub_with_emails:
                sub_with_emails["marked_for_removal"] = (
                    sub_with_emails.get("id") in st.session_state.marked_for_removal
                )
                subscriptions_with_details.append(sub_with_emails)

        progress_bar.empty()
        status_text.empty()

        st.markdown(f"### Found {len(subscriptions_with_details)} Subscriptions")

        for sub in subscriptions_with_details:
            sub["marked_for_removal"] = (
                sub.get("id") in st.session_state.marked_for_removal
            )

            def on_keep(sid):
                st.session_state.marked_for_removal.discard(sid)

            def on_remove(sid):
                st.session_state.marked_for_removal.add(sid)

            def on_generate(sid):
                with st.spinner("Generating description..."):
                    desc = generate_description(sid)
                    if desc:
                        st.session_state.subscriptions = get_subscriptions()

            def on_unsubscribe(sid):
                if unsubscribe(sid):
                    st.success(
                        "Unsubscribe page opened! Complete the process in your browser."
                    )
                else:
                    st.error("Failed to open unsubscribe page")

            updated_sub = render_subscription_card(
                subscription=sub,
                on_generate_description=on_generate,
                on_unsubscribe=on_unsubscribe,
                on_remove=on_remove,
                on_keep=on_keep,
            )

        st.markdown("---")

        marked_count = len(st.session_state.marked_for_removal)

        if marked_count > 0:
            st.warning(f"⚠️ {marked_count} subscription(s) marked for removal")

            if st.button(f"📤 Unsubscribe from {marked_count} Marked"):
                for sub_id in list(st.session_state.marked_for_removal):
                    unsubscribe(sub_id)

                st.session_state.marked_for_removal.clear()
                st.success(
                    "Unsubscribe pages opened! Complete each one in your browser."
                )
                st.rerun()
        else:
            st.info(
                "💡 Use 'Remove' button on subscriptions you want to unsubscribe from"
            )


if __name__ == "__main__":
    main()
