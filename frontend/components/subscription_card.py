import streamlit as st
from datetime import datetime
from typing import Optional


def render_subscription_card(
    subscription: dict,
    expanded: bool = False,
    on_generate_description: Optional[callable] = None,
    on_unsubscribe: Optional[callable] = None,
):
    sub_id = subscription.get("id", "")
    name = subscription.get("name", "Unknown")
    email = subscription.get("email", "")
    unsubscribe_url = subscription.get("unsubscribe_url", "")
    description = subscription.get("description")
    email_count = subscription.get("email_count", 0)
    last_email = subscription.get("last_email_date")
    emails = subscription.get("emails", [])

    if last_email:
        try:
            if isinstance(last_email, str):
                last_date = datetime.fromisoformat(last_email.replace("Z", "+00:00"))
            else:
                last_date = last_email
            last_email_str = last_date.strftime("%b %d, %Y")
        except Exception:
            last_email_str = "Unknown"
    else:
        last_email_str = "Unknown"

    st.markdown("---")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"### {name}")

        if email:
            st.caption(f"📧 From: {email}")

        if description:
            st.caption(f"📝 {description}")
        else:
            st.caption("⏳ *Description generating...*")

        st.caption(f"📧 {email_count} emails • Last: {last_email_str}")

        if unsubscribe_url:
            st.caption(f"🔗 [Unsubscribe link]({unsubscribe_url})")

    with col2:
        if on_unsubscribe and unsubscribe_url:
            if st.button(
                "❌ Unsubscribe", key=f"unsubscribe_{sub_id}", use_container_width=True
            ):
                on_unsubscribe(sub_id)
                st.success(
                    "Opened unsubscribe page. Complete the process in your browser."
                )

    expand_key = f"expand_{sub_id}"

    if expand_key not in st.session_state:
        st.session_state[expand_key] = expanded

    col_label = "▼ Hide emails" if st.session_state[expand_key] else "▶ Show emails"
    if st.button(col_label, key=f"expand_btn_{sub_id}"):
        st.session_state[expand_key] = not st.session_state[expand_key]
        st.rerun()

    if st.session_state.get(expand_key, False) and emails:
        with st.container():
            st.markdown("**Recent emails:**")
            for i, email in enumerate(emails):
                email_date = email.get("date", "Unknown")
                if isinstance(email_date, str):
                    try:
                        email_date = datetime.fromisoformat(
                            email_date.replace("Z", "+00:00")
                        )
                        email_date_str = email_date.strftime("%b %d, %Y")
                    except Exception:
                        email_date_str = email_date
                else:
                    email_date_str = str(email_date)

                with st.expander(
                    f"📧 {email.get('subject', 'No Subject')} - {email_date_str}"
                ):
                    st.markdown(f"**Preview:**")
                    st.text(
                        email.get(
                            "body_preview", email.get("snippet", "No preview available")
                        )
                    )

    if description is None and on_generate_description:
        if st.button("✨ Generate Description", key=f"desc_{sub_id}"):
            on_generate_description(sub_id)
            st.rerun()

    return subscription


def render_scan_controls(
    scan_days: int,
    on_scan_days_change: callable,
    on_scan_click: callable,
    on_rescan_click: callable,
    is_scanning: bool,
    is_authenticated: bool,
):
    st.sidebar.markdown("### Scan Settings")

    days_options = {"30 days": 30, "60 days": 60, "90 days": 90}

    selected = st.sidebar.selectbox(
        "Scan period",
        options=list(days_options.keys()),
        index=0,
        on_change=lambda: on_scan_days_change(
            days_options[
                st.session_state.get("_scan_select", list(days_options.keys())[0])
            ]
        ),
    )

    if on_scan_days_change:
        current_index = (
            list(days_options.keys()).index(selected) if selected in days_options else 0
        )
        new_selection = st.sidebar.selectbox(
            "Scan period",
            options=list(days_options.keys()),
            index=current_index,
            key="_scan_selectbox",
        )
        if new_selection != selected:
            on_scan_days_change(days_options[new_selection])

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button(
            "🔍 Scan",
            use_container_width=True,
            disabled=is_scanning or not is_authenticated,
        ):
            on_scan_click()

    with col2:
        if st.button("🔄 Rescan", use_container_width=True, disabled=is_scanning):
            on_rescan_click()

    return selected
