import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="IT Operations & Ticket Monitoring Dashboard",
    page_icon="🎫",
    layout="wide"
)

# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------
SHEET_ID = "1L6i6dd1DValMG4gN7kcR2Vsve7IfASTtm0yRVXEu34A"

@st.cache_data(ttl=300)
def load_sheet_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    data = pd.read_csv(url)
    data.columns = [c.strip() for c in data.columns]
    return data

try:
    df_form = load_sheet_data("Form%20Responses")
    df_open = load_sheet_data("Open%20Ticket")
except Exception as e:
    st.error("Error loading data from Google Sheets. Please ensure the Google Sheet is shared with 'Anyone with the link can view'.")
    st.stop()

# Data Cleaning & Normalization
for df in [df_form, df_open]:
    if 'Status' in df.columns:
        df['Status'] = df['Status'].astype(str).str.strip().str.capitalize()
    if 'Engineer' in df.columns:
        df['Engineer'] = df['Engineer'].fillna('Unassigned')

# Combine datasets for comprehensive analytics
df_combined = pd.concat([df_form, df_open], ignore_index=True).drop_duplicates(subset=['Job Id'], keep='first')
df_combined['Date_Parsed'] = pd.to_datetime(df_combined['Date'], errors='coerce')

# Split multiple engineers into separate rows for individual workload metrics
df_engineers = df_combined.assign(Engineer=df_combined['Engineer'].str.split(',')).explode('Engineer')
df_engineers['Engineer'] = df_engineers['Engineer'].str.strip()

# ---------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------
st.sidebar.header("🔍 Filters")

status_list = ['All'] + sorted(list(df_combined['Status'].dropna().unique()))
selected_status = st.sidebar.selectbox("Ticket Status", status_list)

engineer_list = ['All'] + sorted(list(df_engineers['Engineer'].dropna().unique()))
selected_engineer = st.sidebar.selectbox("Assigned Engineer", engineer_list)

# Apply global filters for overall charts/metrics
filtered_df = df_combined.copy()
filtered_eng = df_engineers.copy()

if selected_status != 'All':
    filtered_df = filtered_df[filtered_df['Status'] == selected_status]
    filtered_eng = filtered_eng[filtered_eng['Status'] == selected_status]

if selected_engineer != 'All':
    filtered_eng = filtered_eng[filtered_eng['Engineer'] == selected_engineer]
    filtered_df = filtered_df[filtered_df['Job Id'].isin(filtered_eng['Job Id'])]

# ---------------------------------------------------------
# Header & Key Metrics
# ---------------------------------------------------------
st.title("🖥️ IT Operations & Ticket Monitoring Dashboard")
st.markdown("Real-time tracking of support tickets, engineer performance, and resolution status.")

st.markdown("---")

total_tickets = len(filtered_df)
open_tickets = len(filtered_df[filtered_df['Status'] == 'Open'])
closed_tickets = len(filtered_df[filtered_df['Status'] == 'Close'])
closed_rate = (closed_tickets / total_tickets * 100) if total_tickets > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tickets", total_tickets)
col2.metric("Open Tickets", open_tickets)
col3.metric("Closed Tickets", closed_tickets)
col4.metric("Resolution Rate", f"{closed_rate:.1f}%")

st.markdown("---")

# ---------------------------------------------------------
# Charts & Analytics
# ---------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Ticket Status Breakdown")
    status_counts = filtered_df['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    fig_status = px.pie(
        status_counts, 
        names='Status', 
        values='Count', 
        hole=0.4,
        color='Status',
        color_discrete_map={'Open': '#EF553B', 'Close': '#00CC96'}
    )
    fig_status.update_layout(margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_status, use_container_width=True)

with col_right:
    st.subheader("👨‍💻 Tickets Handled by Engineer")
    eng_counts = filtered_eng['Engineer'].value_counts().reset_index()
    eng_counts.columns = ['Engineer', 'Tickets']
    fig_eng = px.bar(
        eng_counts, 
        x='Tickets', 
        y='Engineer', 
        orientation='h',
        text='Tickets',
        color='Tickets',
        color_continuous_scale='Blues'
    )
    fig_eng.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_eng, use_container_width=True)

col_trend, col_system = st.columns(2)

with col_trend:
    st.subheader("📈 Daily Ticket Trend")
    df_trend = filtered_df.groupby(filtered_df['Date_Parsed'].dt.date).size().reset_index(name='Ticket Count')
    fig_trend = px.line(
        df_trend, 
        x='Date_Parsed', 
        y='Ticket Count', 
        markers=True
    )
    fig_trend.update_layout(margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_trend, use_container_width=True)

with col_system:
    st.subheader("💻 Top Reported Systems/Issues")
    sys_counts = filtered_df['System Name'].value_counts().head(10).reset_index()
    sys_counts.columns = ['System Name', 'Count']
    fig_sys = px.bar(
        sys_counts, 
        x='Count', 
        y='System Name', 
        orientation='h',
        text='Count',
        color='Count',
        color_continuous_scale='Purples'
    )
    fig_sys.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_sys, use_container_width=True)

# ---------------------------------------------------------
# Today's Ticket Log Details
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📋 Today's Ticket Log Details")

# Determine Today's Date from dataset / system
today_date = pd.Timestamp.today().normalize()

# Option to toggle between Today's Data and All Data
view_mode = st.radio("Select View Range for Table Log:", ["Today's Data Only", "All Data"], horizontal=True)

if view_mode == "Today's Data Only":
    # If the latest entry in sheet is today, use today, otherwise show latest date available
    latest_date_in_data = filtered_df['Date_Parsed'].max()
    
    # Filter for today (or fallback to latest data date if today has no entries)
    today_df = filtered_df[filtered_df['Date_Parsed'].dt.date == today_date.date()]
    
    if today_df.empty and pd.notnull(latest_date_in_data):
        st.info(f"No tickets found for today ({today_date.strftime('%Y-%m-%d')}). Displaying latest available date ({latest_date_in_data.strftime('%Y-%m-%d')}):")
        display_df = filtered_df[filtered_df['Date_Parsed'].dt.date == latest_date_in_data.date()]
    else:
        display_df = today_df
else:
    display_df = filtered_df

st.dataframe(
    display_df[['Job Id', 'Date', 'System Name', 'Reported By', 'Engineer', 'Issue', 'Status']], 
    use_container_width=True,
    hide_index=True
)
