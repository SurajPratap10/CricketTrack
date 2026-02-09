import streamlit as st
from cricket_parser_v2 import get_db_conn
import pandas as pd

st.set_page_config(
    page_title="Cricket Stats Tracker",
    page_icon="🏏",
    layout="wide"
)

dbname = 'CRICKET_PERF'

# Cache database queries for better performance
@st.cache_data
def get_countries():
    """Get all countries from database"""
    try:
        with get_db_conn(dbname) as sqlite_conn:
            cur = sqlite_conn.cursor()
            cur.execute('SELECT * FROM Countries ORDER BY country')
            col_names = [field[0] for field in cur.description]
            rows = cur.fetchall()
            df = pd.DataFrame(rows, columns=col_names)
            return df
    except Exception as e:
        st.error(f"Error loading countries: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def get_players(country_name=None, match_type=None):
    """Get players by country and match type"""
    try:
        query = """SELECT a.country_id, b.country, a.player_id, a.player, 
                   a.odi_cap, a.t20_cap 
                   FROM Players a 
                   JOIN Countries b ON a.country_id=b.country_id 
                   WHERE"""
        to_filter = []
        conditions = []

        if country_name:
            conditions.append('b.country=?')
            to_filter.append(country_name)
        if match_type:
            conditions.append('a.{}_cap=?'.format(match_type))
            to_filter.append('Y')
        
        if not conditions:
            return pd.DataFrame()
        
        query += ' ' + ' AND '.join(conditions) + ' ORDER BY a.player'
        
        with get_db_conn(dbname) as sqlite_conn:
            cur = sqlite_conn.cursor()
            cur.execute(query, to_filter)
            col_names = [field[0] for field in cur.description]
            rows = cur.fetchall()
            df = pd.DataFrame(rows, columns=col_names)
            return df
    except Exception as e:
        st.error(f"Error loading players: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def get_stats(country_name, play_type, match_type):
    """Get player statistics"""
    try:
        # Normalize match_type
        match_type_upper = match_type.upper()
        if match_type_upper == 'ODI':
            match_type_table = 'Odi'
        elif match_type_upper == 'T20':
            match_type_table = 'T20'
        else:
            return pd.DataFrame()
        
        # Normalize play_type
        play_type_capitalized = play_type.capitalize()
        if play_type_capitalized not in ['Batting', 'Bowling']:
            return pd.DataFrame()
        
        query = """SELECT * FROM {}_Stats_{} 
                   WHERE player IN (
                       SELECT a.player FROM Players a 
                       JOIN Countries b ON a.country_id=b.country_id 
                       WHERE""".format(play_type_capitalized, match_type_table)
        to_filter = []
        conditions = []

        if country_name:
            conditions.append('b.country=?')
            to_filter.append(country_name)
        
        if match_type_upper == 'ODI':
            conditions.append('a.odi_cap=?')
        elif match_type_upper == 'T20':
            conditions.append('a.t20_cap=?')
        to_filter.append('Y')
        
        query += ' ' + ' AND '.join(conditions) + ') ORDER BY player'
        
        with get_db_conn(dbname) as sqlite_conn:
            cur = sqlite_conn.cursor()
            cur.execute(query, to_filter)
            col_names = [field[0] for field in cur.description]
            rows = cur.fetchall()
            df = pd.DataFrame(rows, columns=col_names)
            return df
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")
        return pd.DataFrame()

# Main app
st.title("🏏 Cricket Stats Tracker")
st.markdown("Explore cricket player statistics from around the world")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choose a page",
    ["Countries", "Players", "Statistics"]
)

if page == "Countries":
    st.header("All Countries")
    st.markdown("View all countries in the database")
    
    if st.button("Load Countries", type="primary"):
        with st.spinner("Loading countries..."):
            df = get_countries()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.success(f"Found {len(df)} countries")
            else:
                st.info("No countries found in database")

elif page == "Players":
    st.header("Search Players")
    st.markdown("Search for players by country and match type")
    
    # Get countries for dropdown
    countries_df = get_countries()
    if not countries_df.empty:
        country_list = [''] + sorted(countries_df['country'].tolist())
        selected_country = st.selectbox(
            "Select Country",
            country_list,
            format_func=lambda x: x.replace('-', ' ').title() if x else "All Countries"
        )
        
        match_type = st.selectbox(
            "Match Type",
            ["", "odi", "t20"],
            format_func=lambda x: {"": "All", "odi": "ODI", "t20": "T20"}.get(x, x)
        )
        
        if st.button("Search Players", type="primary"):
            if selected_country:
                with st.spinner("Searching players..."):
                    df = get_players(
                        country_name=selected_country if selected_country else None,
                        match_type=match_type if match_type else None
                    )
                    if not df.empty:
                        st.dataframe(df, use_container_width=True)
                        st.success(f"Found {len(df)} player(s)")
                    else:
                        st.info("No players found")
            else:
                st.warning("Please select a country")
    else:
        st.warning("No countries available. Please load countries first.")

elif page == "Statistics":
    st.header("Player Statistics")
    st.markdown("View detailed batting or bowling statistics")
    
    # Get countries for dropdown
    countries_df = get_countries()
    if not countries_df.empty:
        country_list = sorted(countries_df['country'].tolist())
        selected_country = st.selectbox(
            "Select Country",
            country_list,
            format_func=lambda x: x.replace('-', ' ').title()
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            play_type = st.selectbox(
                "Play Type",
                ["batting", "bowling"]
            )
        
        with col2:
            match_type = st.selectbox(
                "Match Type",
                ["ODI", "T20"]
            )
        
        if st.button("Load Statistics", type="primary"):
            with st.spinner("Loading statistics..."):
                df = get_stats(selected_country, play_type, match_type)
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    st.success(f"Found {len(df)} record(s)")
                    
                    # Show summary statistics
                    st.subheader("Summary")
                    if play_type == "batting":
                        if 'runs_scored' in df.columns:
                            st.metric("Total Runs", df['runs_scored'].sum() if df['runs_scored'].dtype != 'object' else "N/A")
                        if 'batting_average' in df.columns:
                            st.metric("Average", df['batting_average'].mean() if df['batting_average'].dtype != 'object' else "N/A")
                    elif play_type == "bowling":
                        if 'wickets_taken' in df.columns:
                            st.metric("Total Wickets", df['wickets_taken'].sum() if df['wickets_taken'].dtype != 'object' else "N/A")
                        if 'bowling_average' in df.columns:
                            st.metric("Average", df['bowling_average'].mean() if df['bowling_average'].dtype != 'object' else "N/A")
                else:
                    st.info("No statistics found")
    else:
        st.warning("No countries available. Please load countries first.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Cricket Stats Tracker**")
st.sidebar.markdown("Data from ESPN Cricinfo")
