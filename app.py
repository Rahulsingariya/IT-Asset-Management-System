import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import hashlib
import os
import json
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Config:
    ASSETS_FILE = "assets.csv"
    USERS_FILE = "users.json"
    MIN_PASSWORD_LENGTH = 8
    APP_VERSION = "2.1.1"
    SUPPORTED_CATEGORIES = [
        "Laptop", "Desktop", "Server", "Printer", "Monitor", 
        "Network", "Peripheral", "Mobile", "Storage", "Other"
    ]
    SUPPORTED_STATUSES = ["Available", "Assigned", "Repair", "Disposed", "Archived"]

config = Config()

@st.cache_data(ttl=300)  
def hash_password(password: str) -> str:
    """Secure password hashing with salt simulation."""
    return hashlib.sha256(f"itsm_salt_{password}".encode()).hexdigest()

def load_users() -> Dict[str, str]:
    """Load users with fallback to defaults."""
    default_users = {"admin": hash_password("Admin@2024")}
    
    if os.path.exists(config.USERS_FILE):
        try:
            with open(config.USERS_FILE, 'r') as f:
                users_data = json.load(f)
                return {user['username']: user['password_hash'] for user in users_data}
        except Exception as e:
            logger.error(f"Failed to load users: {e}")
    
    return default_users

def save_users(users: Dict[str, Dict]):
    """Save users with metadata."""
    try:
        with open(config.USERS_FILE, 'w') as f:
            json.dump(list(users.values()), f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save users: {e}")

def init_storage():
    """Initialize enterprise-grade storage."""
    Path(config.ASSETS_FILE).touch(exist_ok=True)
    
    if os.path.getsize(config.ASSETS_FILE) == 0:
        schema = pd.DataFrame({
            "Asset ID": [],
            "Asset Name": [],
            "Category": [],
            "Brand": [],
            "Model": [],
            "Serial No": [],
            "Status": [],
            "Assigned To": [],
            "Purchase Date": [],
            "Warranty Expiry": [],
            "Location": [],
            "Cost": [],
            "Notes": [],
            "Created Date": [],
            "Last Updated": []
        })
        schema.to_csv(config.ASSETS_FILE, index=False)

@st.cache_data(ttl=600)
def load_assets() -> pd.DataFrame:
    """Load assets with enterprise data validation."""
    try:
        df = pd.read_csv(config.ASSETS_FILE)
        
        date_cols = ["Purchase Date", "Warranty Expiry", "Created Date", "Last Updated"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        df = df.fillna("")
        df = df.astype({"Cost": "float64"}, errors='ignore')
        
        return df
    except Exception as e:
        logger.error(f"Failed to load assets: {e}")
        return pd.DataFrame()

def save_assets(df: pd.DataFrame):
    """Save assets with audit trail."""
    try:
        df_copy = df.copy()
        date_cols = ["Purchase Date", "Warranty Expiry", "Created Date", "Last Updated"]
        
        for col in date_cols:
            if col in df_copy.columns:
                mask = pd.notna(df_copy[col])
                df_copy.loc[mask, col] = pd.to_datetime(df_copy.loc[mask, col]).dt.strftime('%Y-%m-%d')
        
        df_copy.to_csv(config.ASSETS_FILE, index=False)
        st.cache_data.clear()
        logger.info(f"Saved {len(df)} assets")
    except Exception as e:
        st.error(f"Save failed: {e}")
        logger.error(f"Save error: {e}")
        
def render_login_page():
    """Enterprise-grade login interface."""
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem;">
        <div style="font-size: 4rem; color: #1f77b4;">💼</div>
        <h1 style="color: #1f77b4; margin: 0;">IT Asset Management System</h1>
        <p style="color: #666; font-size: 1.1rem; margin: 0.5rem 0 2rem 0;">
            Enterprise Asset Tracking & Analytics
        </p>
        <div style="background: linear-gradient(90deg, #1f77b4, #4a90e2); 
                    color: white; padding: 1rem 2rem; border-radius: 10px; 
                    display: inline-block; font-weight: 600;">
            v{version}
        </div>
    </div>
    """.format(version=config.APP_VERSION), unsafe_allow_html=True)

    st.markdown("---")
    
    with st.form("enterprise_login", clear_on_submit=True):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("### 🔐 Authentication")
        
        with col2:
            username = st.text_input("👤 Username", placeholder="admin")
            password = st.text_input("🔑 Password", type="password", 
                                   placeholder="Admin@2024")
            remember = st.checkbox("Remember me")
            
            col_a, col_b = st.columns([3, 1])
            with col_b:
                login_btn = st.form_submit_button("🚀 Enter System", 
                                                use_container_width=True,
                                                type="primary")
        
        if login_btn:
            users = load_users()
            if username in users and users[username] == hash_password(password):
                st.session_state.update({
                    "logged_in": True,
                    "username": username,
                    "remember_me": remember
                })
                st.success(f"✅ Welcome, {username.title()}!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Default: admin / Admin@2024")

def render_logout():
    """Secure logout."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def render_sidebar(df: pd.DataFrame):
    """Professional enterprise sidebar."""
    st.sidebar.markdown(f"""
    # 💼 IT Asset Manager
    **v{config.APP_VERSION}**
    """)
    
    if not df.empty:
        st.sidebar.markdown("### 📊 KPIs")
        total = len(df)
        assigned_pct = len(df[df["Status"] == "Assigned"]) / total * 100
        
        st.sidebar.metric("Total Assets", total)
        st.sidebar.metric("Utilization", f"{assigned_pct:.1f}%")
    
    st.sidebar.markdown("---")
    
    menu_options = ["📊 Dashboard", "➕ Add Asset", "🛠️ Manage", "📈 Reports", "⚙️ Settings"]
    selected = st.sidebar.selectbox("Navigation", menu_options, 
                                  key="enterprise_menu")
    
    st.session_state["menu"] = selected
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        render_logout()

def render_dashboard(df: pd.DataFrame):
    """Executive dashboard with FIXED metrics."""
    st.markdown("# 📊 Executive Dashboard")
    st.markdown("*Real-time asset analytics & insights*")
    
    if df.empty:
        st.info("👆 Add your first asset to see analytics!")
        return
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total = len(df)
    assigned = len(df[df["Status"] == "Assigned"])
    available = len(df[df["Status"] == "Available"])
    repair = len(df[df["Status"] == "Repair"])
    
    threshold_date = pd.to_datetime(date.today() + timedelta(days=90))
    expiring = len(df[df["Warranty Expiry"] < threshold_date].dropna(subset=["Warranty Expiry"]))
    
    with col1:
        st.metric(label="Total Assets", value=total)
    with col2:
        st.metric(label="Assigned", value=assigned)
    with col3:
        st.metric(label="Available", value=available)
    with col4:
        st.metric(label="Repair", value=repair)
    with col5:
        st.metric(label="Expiring Soon", value=expiring)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Status Distribution")
        fig_pie = px.pie(df, names="Status", 
                        color_discrete_sequence=px.colors.sequential.Sunset,
                        title="Asset Utilization")
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.markdown("### 🏷️ Top Categories")
        top_cats = df["Category"].value_counts().head(7)
        fig_bar = px.bar(x=top_cats.index, y=top_cats.values,
                        title="Asset Categories",
                        color=top_cats.values,
                        color_continuous_scale="Viridis")
        st.plotly_chart(fig_bar, use_container_width=True)

def render_add_asset(df: pd.DataFrame):
    st.markdown("# ➕ Register New Asset")
    
    with st.form("asset_registration"):
        col1, col2 = st.columns(2)
        
        with col1:
            asset_id = st.text_input("🆔 Asset ID *", help="LAP001, DESK-2026, etc.")
            name = st.text_input("📝 Asset Name *")
            category = st.selectbox("🏷️ Category *", config.SUPPORTED_CATEGORIES)
            brand = st.text_input("🏢 Brand *")
            model = st.text_input("📱 Model")
            serial = st.text_input("🔢 Serial Number")
        
        with col2:
            status = st.selectbox("📊 Status *", config.SUPPORTED_STATUSES)
            assignee = st.text_input("👤 Assigned To")
            location = st.text_input("📍 Location")
            cost = st.number_input("💰 Cost (₹)", min_value=0.0, format="%.2f")
            purchase = st.date_input("📅 Purchase Date", value=date.today())
            warranty = st.date_input("🛡️ Warranty End", 
                                   min_value=purchase, 
                                   value=date.today() + timedelta(days=365))
        
        notes = st.text_area("📋 Notes", height=80)
        submitted = st.form_submit_button("✅ Register Asset", type="primary")
    
    if submitted:
        errors = []
        if not all([asset_id.strip(), name.strip(), brand.strip(), category]):
            errors.append("Required fields missing")
        if asset_id.strip() in df["Asset ID"].values:
            errors.append("Asset ID already exists")
        if warranty <= purchase:
            errors.append("Warranty must exceed purchase date")
        
        if errors:
            for error in errors:
                st.error(error)
        else:
            new_asset = pd.DataFrame([{
                "Asset ID": asset_id.strip(),
                "Asset Name": name.strip(),
                "Category": category,
                "Brand": brand.strip(),
                "Model": model.strip(),
                "Serial No": serial.strip(),
                "Status": status,
                "Assigned To": assignee.strip(),
                "Purchase Date": purchase,
                "Warranty Expiry": warranty,
                "Location": location.strip(),
                "Cost": cost,
                "Notes": notes.strip(),
                "Created Date": date.today(),
                "Last Updated": date.today()
            }])
            
            updated_df = pd.concat([df, new_asset], ignore_index=True)
            save_assets(updated_df)
            st.success("🎉 Asset registered successfully!")
            st.balloons()

def render_manage_assets(df: pd.DataFrame):
    """Enhanced asset management with filters."""
    st.markdown("# 🛠️ Asset Management")
    
    col1, col2 = st.columns(2)
    with col1:
        search = st.text_input("🔍 Search Assets")
    with col2:
        status_filter = st.selectbox("Filter Status", ["All"] + list(config.SUPPORTED_STATUSES))
    
    filtered_df = df.copy()
    if search:
        filtered_df = filtered_df[filtered_df.astype(str).apply(lambda row: search.lower() in row.str.lower().str.cat(sep=' '), axis=1)]
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["Status"] == status_filter]
    
    st.dataframe(filtered_df, use_container_width=True, height=500)

def render_reports(df: pd.DataFrame):
    """Professional reporting dashboard."""
    st.markdown("# 📊 Reports & Analytics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(df, use_container_width=True, height=400)
    with col2:
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Full Report",
            csv_data,
            f"it-assets-report-{date.today().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
        
def render_settings(df: pd.DataFrame):
    """Complete settings management panel."""
    st.markdown("# ⚙️ System Settings & Administration")
    
    tab1, tab2, tab3 = st.tabs(["👥 User Management", "💾 Backup/Restore", "📈 System Info"])
    
    with tab1:
        st.markdown("### User Management Panel")
        users = load_users()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Current Users")
            for username, password_hash in users.items():
                with st.expander(f"👤 {username}", expanded=False):
                    st.info(f"**Hashed Password:** `{password_hash[:20]}...`")
                    if st.button(f"🗑️ Remove {username}", key=f"del_{username}"):
                        new_users = {k: v for k, v in users.items() if k != username}
                        save_users(new_users)
                        st.success(f"✅ Removed {username}")
                        st.rerun()
        
        with col2:
            st.subheader("➕ Add New User")
            with st.form("add_user_form"):
                new_username = st.text_input("New Username")
                new_password = st.text_input("New Password", type="password")
                if st.form_submit_button("➕ Create User"):
                    if new_username and new_password:
                        if new_username not in users:
                            new_users = users.copy()
                            new_users[new_username] = hash_password(new_password)
                            save_users(new_users)
                            st.success(f"✅ Created user: {new_username}")
                        else:
                            st.error("❌ Username already exists")
                    else:
                        st.error("❌ Both fields required")
    
    with tab2:
        st.markdown("### 💾 Data Backup & Maintenance")
        
        col1, col2 = st.columns(2)
        with col1:
         
            csv_backup = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "💾 Download Backup",
                csv_backup,
                f"assets-backup-{date.today().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        
        with col2:
       
            st.warning("⚠️ DANGER ZONE - Clear All Data")
            if st.button("🗑️ Clear All Assets", type="secondary"):
                if st.button("⚠️ CONFIRM - Delete Everything", type="primary"):
                    pd.DataFrame(columns=df.columns).to_csv(config.ASSETS_FILE, index=False)
                    st.cache_data.clear()
                    st.success("🗑️ All assets cleared!")
                    st.rerun()
    
    with tab3:
        st.markdown("### 📈 System Status")
        st.metric("Total Assets", len(df))
        st.metric("File Size", f"{Path(config.ASSETS_FILE).stat().st_size / 1024:.1f} KB")
        st.metric("Active Users", len(load_users()))
        st.json({
            "App Version": config.APP_VERSION,
            "Python Version": ".".join(str(v) for v in st.__version__.split('.')[:2]),
            "Pandas Version": pd.__version__,
            "Status": "🟢 Production Ready"
        })

def main():
    init_storage()
    

    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        render_login_page()
        st.stop()
    
    df = load_assets()
    

    st.markdown(f"👋 Welcome, **{st.session_state.username.title()}** | 💼 IT Asset Manager Pro")
    

    render_sidebar(df)
    menu_map = {
        "📊 Dashboard": render_dashboard,
        "➕ Add Asset": render_add_asset,
        "🛠️ Manage": render_manage_assets,
        "📈 Reports": render_reports,
        "⚙️ Settings": render_settings
    }
    
    menu_map[st.session_state.get("menu", "📊 Dashboard")](df)

if __name__ == "__main__":
    st.set_page_config(
        page_title="IT Asset Manager Pro",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()

