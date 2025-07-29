import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Surgeon Schedule Viewer",
    layout="wide"
)

# --- Database Connection ---
@st.cache_resource
def get_connection():
    """Creates and caches a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  
            password='_________',  # Replace with MySQL password
            database='Final_Project'
        )
        return connection
    except mysql.connector.Error as err:
        st.error(f"Error connecting to database: {err}")
        # Stop the app if the database connection fails.
        st.stop()

# --- Main Application UI ---
st.title("Pediatric Urology Provider Schedule")
st.markdown("Use the filters below to find provider schedules for a specific date, location, and role.")

conn = get_connection()

# --- Sidebar for Filters ---
st.sidebar.header("🗓️ Filter Options")

# Date selector widget in the sidebar.
schedule_date = st.sidebar.date_input(
    "Select a Date",
    value=datetime(2025, 7, 16)
)

# --- Dynamic Location Filters (with TRIM to prevent whitespace errors) ---
@st.cache_data(ttl=600)
def get_locations_by_type(_conn, type_name):
    """Fetches and caches locations based on their activity type, trimming whitespace."""
    query = """
        SELECT TRIM(l.location_name) AS location_name
        FROM locations l
        JOIN activity_types at ON l.activity_type_id = at.activity_type_id
        WHERE at.activity_name = %s
        ORDER BY location_name;
    """
    df = pd.read_sql(query, _conn, params=[type_name])
    return df['location_name'].tolist()

@st.cache_data(ttl=600)
def get_all_locations(_conn):
    """Fetches and caches all unique location names, trimming whitespace."""
    query = "SELECT DISTINCT TRIM(location_name) AS location_name FROM locations ORDER BY location_name;"
    df = pd.read_sql(query, _conn)
    return df['location_name'].tolist()

# Get lists of ORs and Clinics
or_locations = get_locations_by_type(conn, 'OR')
clinic_locations = get_locations_by_type(conn, 'Clinic')
all_locations = get_all_locations(conn)

st.sidebar.markdown("---")
st.sidebar.markdown("##### Location Filters")

# Use columns for the buttons for a cleaner layout
row1_col1, row1_col2 = st.sidebar.columns(2)
row2_col1, row2_col2 = st.sidebar.columns(2)

# Initialize session state for selected locations if it doesn't exist
if 'selected_locations' not in st.session_state:
    st.session_state.selected_locations = or_locations # Default to ORs

with row1_col1:
    if st.button("All ORs", use_container_width=True):
        st.session_state.selected_locations = or_locations
with row1_col2:
    if st.button("All Clinics", use_container_width=True):
        st.session_state.selected_locations = clinic_locations
with row2_col1:
    if st.button("Select All", use_container_width=True):
        st.session_state.selected_locations = all_locations
with row2_col2:
    if st.button("Deselect All", use_container_width=True):
        st.session_state.selected_locations = []


# Before rendering the multiselect, ensure all its default values exist in the options.
valid_selections = [loc for loc in st.session_state.selected_locations if loc in all_locations]
st.session_state.selected_locations = valid_selections

# Location multi-select widget in the sidebar.
selected_locations = st.sidebar.multiselect(
    "Select or Deselect Locations",
    options=all_locations,
    key='selected_locations'
)
st.sidebar.markdown("---")

# --- Role Filter ---
st.sidebar.markdown("##### Role Filters")
all_roles = ['S', 'NP']

if 'selected_roles' not in st.session_state:
    st.session_state.selected_roles = all_roles

role_col1, role_col2 = st.sidebar.columns(2)
with role_col1:
    if st.button("Select All Roles", use_container_width=True):
        st.session_state.selected_roles = all_roles
with role_col2:
    if st.button("Deselect All Roles", use_container_width=True):
        st.session_state.selected_roles = []


selected_roles = st.sidebar.multiselect(
    "Select Provider Roles",
    options=all_roles,
    key='selected_roles'
)


# --- Display Schedule Data ---
st.header(f"Schedule for: {schedule_date.strftime('%A, %B %d, %Y')}")

# Only run the query and display data if the user has selected at least one location and role.
if not selected_locations or not selected_roles:
    st.warning("Please select at least one location and one role from the sidebar to view the schedule.")
else:
    try:
        # --- DYNAMIC QUERY LOGIC ---
        loc_placeholders = ', '.join(['%s'] * len(selected_locations))
        role_placeholders = ', '.join(['%s'] * len(selected_roles))

        query = f"""
        SELECT
            p.initials AS "Initials",
            p.role AS "Role",
            l.location_name AS "Location",
            si.session AS "Session (AM/PM/FD)",
            si.notes AS "Notes"
        FROM schedule_instances si
        JOIN providers p ON si.provider_id = p.provider_id
        JOIN locations l ON si.location_id = l.location_id
        WHERE
            si.schedule_date = %s
            AND l.location_name IN ({loc_placeholders})
            AND p.role IN ({role_placeholders})
        ORDER BY
            l.location_name, p.initials;
        """

        # Create the list of parameters to pass to the query.
        params = [schedule_date] + selected_locations + selected_roles
        
        # Execute the query with the correctly formatted parameters.
        schedule_df = pd.read_sql(query, conn, params=params)

        # Display the results.
        if schedule_df.empty:
            st.info("No schedules found for the selected date, locations, and roles.")
        else:
            # Display the DataFrame as a styled table.
            st.dataframe(schedule_df, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred while querying the database: {e}")

