import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="IT Service Request Dashboard",
    page_icon="🛠️",
    layout="wide"
)

# ---------------------------------------------------------
# Load Data from Google Sheets
# ---------------------------------------------------------
SHEET_ID = "1O8PBe6lltp5SprO8aUhTYpJoHbB5fDSWLcMa3NLfjc4"

@st.cache_data(ttl=300)
def load_sheet_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    data = pd.read_csv(url)
    data.columns = [c.strip() for c in data.columns]
    return data

try:
    df_main = load_sheet_data("Main")
    df_open = load_sheet_data("Open%20Ticket")
except Exception as e:
    st.error("Error loading data from Google Sheets. Ensure the Google Sheet is shared with 'Anyone with the link can view'.")
    st.stop()

# Combine datasets for comprehensive analysis
df_combined = pd.concat([df_main, df_open], ignore_index=True).drop_duplicates(subset=['Ticket Id'], keep='first')

# Clean Column Names & Values
if 'Status' in df_combined.columns:
    df_combined['Status'] = df_combined['Status'].fillna('Unassigned').astype(str).str.strip().str.title()

if 'Engineer Name' in df_combined.columns:
    df_combined['Engineer Name'] = df_combined['Engineer Name'].fillna('Unassigned').astype(str)

if 'Issue category' in df_combined.columns:
    df_combined['Issue category'] = df_combined['Issue category'].fillna('Other').astype(str)

# Parse Date
df_combined['Date_Parsed'] = pd.to_datetime(df_combined['Date'], errors='coerce')

# Split multiple engineers assigned to a single ticket into separate rows for metrics
df_engineers = df_combined.assign(Engineer=df_combined['Engineer Name'].str.split(',')).explode('Engineer')
df_engineers['Engineer'] = df_engineers['Engineer'].str.strip()

# ---------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------
st.sidebar.header("🔍 Filters")

status_list = ['All'] + sorted(list(df_combined['Status'].dropna().unique()))
selected_status = st.sidebar.selectbox("Ticket Status", status_list)

engineer_list = ['All'] + sorted(list(df_engineers['Engineer'].dropna().unique()))
selected_engineer = st.sidebar.selectbox("Assigned Engineer", engineer_list)

category_list = ['All'] + sorted(list(df_combined['Issue category'].dropna().unique()))
selected_category = st.sidebar.selectbox("Issue Category", category_list)

# Apply Filters
filtered_df = df_combined.copy()
filtered_eng = df_engineers.copy()

if selected_status != 'All':
    filtered_df = filtered_df[filtered_df['Status'] == selected_status]
    filtered_eng = filtered_eng[filtered_eng['Status'] == selected_status]

if selected_engineer != 'All':
    filtered_eng = filtered_eng[filtered_eng['Engineer'] == selected_engineer]
    id_col = 'Ticket Id' if 'Ticket Id' in filtered_df.columns else 'Job Id'
    filtered_df = filtered_df[filtered_df[id_col].isin(filtered_eng[id_col])]

if selected_category != 'All':
    filtered_df = filtered_df[filtered_df['Issue category'] == selected_category]
    filtered_eng = filtered_eng[filtered_eng['Issue category'] == selected_category]

# ---------------------------------------------------------
# Header & Embedded Google Form
# ---------------------------------------------------------
st.title("🖥️ IT Service Request Dashboard")
st.markdown("Real-time tracking of service desk tickets, issue categories, and engineer performance.")

# Embedded Google Form inside a clean expander section
with st.expander("📝 Submit a New IT Service Request (Google Form)", expanded=False):
    st.markdown("Fill out the form below to submit a new service request directly to the helpdesk:")
    components.iframe(
        "https://docs.google.com/forms/d/e/1FAIpQLScJjEzt6LVcGG0kRNhdSn-fWo1D6pJbOBYvBsrgzg2ivy5bcw/viewform?embedded=true",
        height=650,
        scrolling=True
    )

st.markdown("---")

# ---------------------------------------------------------
# Key Metrics
# ---------------------------------------------------------
total_tickets = len(filtered_df)
open_tickets = len(filtered_df[filtered_df['Status'].isin(['New', 'Assigned', 'In Progress', 'Pending'])])
closed_tickets = len(filtered_df[filtered_df['Status'] == 'Closed'])
closed_rate = (closed_tickets / total_tickets * 100) if total_tickets > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tickets", total_tickets)
col2.metric("Open/Pending Tickets", open_tickets)
col3.metric("Closed Tickets", closed_tickets)
col4.metric("Resolution Rate", f"{closed_rate:.1f}%")

st.markdown("---")

# ---------------------------------------------------------
# Charts & Visualizations
# ---------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Ticket Status Distribution")
    status_counts = filtered_df['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    fig_status = px.pie(
        status_counts, 
        names='Status', 
        values='Count', 
        hole=0.4,
        color='Status',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_status.update_layout(margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_status, use_container_width=True)

with col_right:
    st.subheader("👨‍💻 Workload by Engineer")
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

col_trend, col_cat = st.columns(2)

with col_trend:
    st.subheader("📈 Ticket Trend Over Time")
    df_trend = filtered_df.groupby(filtered_df['Date_Parsed'].dt.date).size().reset_index(name='Ticket Count')
    fig_trend = px.line(
        df_trend, 
        x='Date_Parsed', 
        y='Ticket Count', 
        markers=True
    )
    fig_trend.update_layout(margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_trend, use_container_width=True)

with col_cat:
    st.subheader("🏷️ Issue Categories Breakdown")
    cat_counts = filtered_df['Issue category'].value_counts().reset_index()
    cat_counts.columns = ['Category', 'Count']
    fig_cat = px.bar(
        cat_counts, 
        x='Category', 
        y='Count', 
        text='Count',
        color='Category',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_cat.update_layout(margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_cat, use_container_width=True)

# ---------------------------------------------------------
# Ticket Log Details
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📋 Ticket Log Details")

today_date = pd.Timestamp.today().normalize()
view_mode = st.radio("Select View Range for Log Table:", ["Today's Data Only", "All Data"], horizontal=True)

if view_mode == "Today's Data Only":
    latest_date_in_data = filtered_df['Date_Parsed'].max()
    today_df = filtered_df[filtered_df['Date_Parsed'].dt.date == today_date.date()]
    
    if today_df.empty and pd.notnull(latest_date_in_data):
        st.info(f"No tickets logged for today ({today_date.strftime('%Y-%m-%d')}). Displaying latest available date ({latest_date_in_data.strftime('%Y-%m-%d')}):")
        display_df = filtered_df[filtered_df['Date_Parsed'].dt.date == latest_date_in_data.date()]
    else:
        display_df = today_df
else:
    display_df = filtered_df

columns_to_show = [col for col in ['Ticket Id', 'Date', 'Employee Name', 'Department Name', 'System Name', 'Issue category', 'Status', 'Engineer Name'] if col in display_df.columns]

st.dataframe(
    display_df[columns_to_show], 
    use_container_width=True,
    hide_index=True
)
