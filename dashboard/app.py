import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
import os
import sys

# Add parent directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models import MessageLog, DlrLog

# Configure Streamlit page
st.set_page_config(
    page_title="LINE LON Integration Dashboard",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling using HTML inside markdown
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        color: #06C755; /* LINE Green */
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">💬 LINE Official Notification (LON)</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Thai Watsadu Integration Monitoring Portal & Logs Dashboard</div>', unsafe_allow_html=True)

# Database Query Helper
def get_logs_df():
    db = SessionLocal()
    try:
        query = db.query(MessageLog).order_by(MessageLog.created_at.desc())
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

def get_dlr_logs_for_msg(message_log_id):
    db = SessionLocal()
    try:
        query = db.query(DlrLog).filter(DlrLog.message_log_id == message_log_id).order_by(DlrLog.received_at.desc())
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

# Load Data
try:
    df_logs = get_logs_df()
except Exception as e:
    st.error(f"Failed to connect to the database. Make sure you run the FastAPI server first to initialize the database tables. Error: {str(e)}")
    st.stop()

# Sidebar Filters
st.sidebar.header("🔍 Filter Messages")
env_filter = st.sidebar.multiselect("Environment", options=["test", "prod"], default=["test", "prod"])
status_filter = st.sidebar.multiselect(
    "Delivery Status", 
    options=["pending", "delivered", "undeliverable", "fallback_sms_sent", "api_failed_triggered_sms"],
    default=["pending", "delivered", "undeliverable", "fallback_sms_sent", "api_failed_triggered_sms"]
)
phone_search = st.sidebar.text_input("Search by Phone (e.g. 66812345678)")

# Apply filters
filtered_df = df_logs.copy()
if env_filter:
    filtered_df = filtered_df[filtered_df['env_mode'].isin(env_filter)]
if status_filter:
    filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
if phone_search:
    filtered_df = filtered_df[filtered_df['phone_number'].str.contains(phone_search, case=False, na=False)]

# Main Metrics Row
total_sent = len(df_logs)
delivered = len(df_logs[df_logs['status'] == 'delivered'])
failed = len(df_logs[df_logs['status'] == 'undeliverable'])
sms_fallback = len(df_logs[df_logs['status'] == 'fallback_sms_sent'])
pending = len(df_logs[df_logs['status'] == 'pending'])

success_rate = (delivered / (total_sent - pending) * 100) if (total_sent - pending) > 0 else 100.0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Processed", f"{total_sent}")
with col2:
    st.metric("Delivered (LINE)", f"{delivered}", delta=f"{success_rate:.1f}% Success" if total_sent > 0 else None)
with col3:
    st.metric("Delivery Failed", f"{failed}")
with col4:
    st.metric("SMS Fallback Sent", f"{sms_fallback}")
with col5:
    st.metric("Pending DLR", f"{pending}")

st.markdown("---")

# Main Section: Logs Table
st.subheader("📋 Message Logs Table")

if filtered_df.empty:
    st.info("No message logs match the selected filters.")
else:
    # Format dates
    display_df = filtered_df.copy()
    display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df['updated_at'] = pd.to_datetime(display_df['updated_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Select columns to display
    display_cols = [
        'id', 'phone_number', 'template_type', 'env_mode', 
        'status', 'external_msg_id', 'created_at', 'updated_at'
    ]
    
    # Download CSV Button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Filtered Logs to CSV",
        data=csv,
        file_name="lon_integration_logs.csv",
        mime="text/csv",
    )
    
    # Display table
    st.dataframe(display_df[display_cols], use_container_width=True, hide_index=True)

    # Detailed Inspect Section
    st.markdown("---")
    st.subheader("🔍 Inspect Message & Webhook Logs")
    
    selected_id = st.selectbox(
        "Select a Transaction ID to view details and webhook delivery history:",
        options=filtered_df['id'].tolist()
    )
    
    if selected_id:
        selected_row = filtered_df[filtered_df['id'] == selected_id].iloc[0]
        
        det_col1, det_col2 = st.columns(2)
        with det_col1:
            st.markdown("**Message Details**")
            st.write(f"- **Transaction ID:** `{selected_row['id']}`")
            st.write(f"- **Phone Number:** `{selected_row['phone_number']}`")
            st.write(f"- **Template Type:** `{selected_row['template_type']}`")
            st.write(f"- **Template UUID:** `{selected_row['template_id']}`")
            st.write(f"- **Environment:** `{selected_row['env_mode'].upper()}`")
            st.write(f"- **Status:** `{selected_row['status']}`")
            st.write(f"- **External EGG Message ID:** `{selected_row['external_msg_id']}`")
            
        with det_col2:
            st.markdown("**Message Payload & Fallback**")
            st.json(selected_row['payload'])
            if selected_row['sms_fallback_text']:
                st.info(f"**SMS Fallback Text:** {selected_row['sms_fallback_text']}")
            else:
                st.warning("No SMS fallback text configured for this message.")

        # DLR Webhook logs
        st.markdown("##### 📡 Webhook Delivery Events (DLR Logs)")
        dlr_df = get_dlr_logs_for_msg(selected_id)
        if dlr_df.empty:
            st.info("No DLR events received for this message yet.")
        else:
            dlr_df['received_at'] = pd.to_datetime(dlr_df['received_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(
                dlr_df[['received_at', 'status_group_id', 'status_group_name', 'status_name', 'status_description', 'error_name', 'event_time']],
                use_container_width=True,
                hide_index=True
            )
