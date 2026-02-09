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

@st.cache_data
def get_player_details(player_name):
    """Get all statistics for a specific player"""
    try:
        player_stats = {}
        
        # Get batting stats for ODI
        with get_db_conn(dbname) as sqlite_conn:
            cur = sqlite_conn.cursor()
            cur.execute("SELECT * FROM Batting_Stats_Odi WHERE player=?", (player_name,))
            col_names = [field[0] for field in cur.description] if cur.description else []
            rows = cur.fetchall()
            if rows:
                player_stats['batting_odi'] = pd.DataFrame(rows, columns=col_names)
            else:
                player_stats['batting_odi'] = pd.DataFrame()
            
            # Get batting stats for T20
            cur.execute("SELECT * FROM Batting_Stats_T20 WHERE player=?", (player_name,))
            col_names = [field[0] for field in cur.description] if cur.description else []
            rows = cur.fetchall()
            if rows:
                player_stats['batting_t20'] = pd.DataFrame(rows, columns=col_names)
            else:
                player_stats['batting_t20'] = pd.DataFrame()
            
            # Get bowling stats for ODI
            cur.execute("SELECT * FROM Bowling_Stats_Odi WHERE player=?", (player_name,))
            col_names = [field[0] for field in cur.description] if cur.description else []
            rows = cur.fetchall()
            if rows:
                player_stats['bowling_odi'] = pd.DataFrame(rows, columns=col_names)
            else:
                player_stats['bowling_odi'] = pd.DataFrame()
            
            # Get bowling stats for T20
            cur.execute("SELECT * FROM Bowling_Stats_T20 WHERE player=?", (player_name,))
            col_names = [field[0] for field in cur.description] if cur.description else []
            rows = cur.fetchall()
            if rows:
                player_stats['bowling_t20'] = pd.DataFrame(rows, columns=col_names)
            else:
                player_stats['bowling_t20'] = pd.DataFrame()
        
        return player_stats
    except Exception as e:
        st.error(f"Error loading player details: {str(e)}")
        return {}

@st.cache_data
def get_all_players_list():
    """Get list of all players"""
    try:
        with get_db_conn(dbname) as sqlite_conn:
            cur = sqlite_conn.cursor()
            cur.execute("SELECT DISTINCT player FROM Players ORDER BY player")
            rows = cur.fetchall()
            return [row[0] for row in rows] if rows else []
    except Exception as e:
        return []

# Main app
st.title("🏏 Cricket Stats Tracker")
st.markdown("Explore cricket player statistics from around the world")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choose a page",
    ["Countries", "Players", "Statistics", "Player Details"]
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
                        
                        # Allow selecting a player to view details
                        st.markdown("---")
                        st.markdown("### View Player Details")
                        player_names = df['player'].tolist()
                        selected_player_for_details = st.selectbox(
                            "Select a player to view full statistics",
                            player_names,
                            key="player_details_select"
                        )
                        if st.button("View Full Statistics", type="primary", key="view_player_stats"):
                            st.session_state['selected_player'] = selected_player_for_details
                            st.session_state['page'] = 'Player Details'
                            st.rerun()
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

elif page == "Player Details":
    st.header("👤 Player Statistics")
    st.markdown("Select a player to view their complete statistics")
    
    # Get all players
    players_list = get_all_players_list()
    
    if players_list:
        # Check if player was selected from Players page
        default_index = 0
        if 'selected_player' in st.session_state and st.session_state['selected_player'] in players_list:
            default_index = players_list.index(st.session_state['selected_player'])
            # Clear the session state after using it
            del st.session_state['selected_player']
        
        selected_player = st.selectbox(
            "Select Player",
            players_list,
            index=default_index
        )
        
        if selected_player:
            with st.spinner("Loading player statistics..."):
                player_stats = get_player_details(selected_player)
                
                # Player header
                st.markdown("---")
                st.markdown(f"## 🏏 {selected_player}")
                st.markdown("---")
                
                # Create tabs for different views
                tab1, tab2, tab3, tab4 = st.tabs(["📊 Batting - ODI", "📊 Batting - T20", "🎯 Bowling - ODI", "🎯 Bowling - T20"])
                
                # Batting ODI Tab
                with tab1:
                    if not player_stats.get('batting_odi', pd.DataFrame()).empty:
                        df = player_stats['batting_odi']
                        st.subheader("ODI Batting Statistics")
                        
                        # Key metrics in columns
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            runs = df['runs_scored'].iloc[0] if 'runs_scored' in df.columns else "N/A"
                            st.metric("Total Runs", runs)
                        
                        with col2:
                            avg = df['batting_average'].iloc[0] if 'batting_average' in df.columns else "N/A"
                            st.metric("Batting Average", avg)
                        
                        with col3:
                            matches = df['matches_played'].iloc[0] if 'matches_played' in df.columns else "N/A"
                            st.metric("Matches", matches)
                        
                        with col4:
                            sr = df['batting_strike_rate'].iloc[0] if 'batting_strike_rate' in df.columns else "N/A"
                            st.metric("Strike Rate", sr)
                        
                        # More metrics
                        col5, col6, col7, col8 = st.columns(4)
                        
                        with col5:
                            hundreds = df['hundreds_scored'].iloc[0] if 'hundreds_scored' in df.columns else "N/A"
                            st.metric("Hundreds", hundreds)
                        
                        with col6:
                            fifties = df['scores_between_50_and_99'].iloc[0] if 'scores_between_50_and_99' in df.columns else "N/A"
                            st.metric("Fifties", fifties)
                        
                        with col7:
                            hs = df['highest_innings_score'].iloc[0] if 'highest_innings_score' in df.columns else "N/A"
                            st.metric("Highest Score", hs)
                        
                        with col8:
                            sixes = df['boundary_sixes'].iloc[0] if 'boundary_sixes' in df.columns else "N/A"
                            st.metric("Sixes", sixes)
                        
                        # Full table
                        st.markdown("### Complete Statistics")
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No ODI batting statistics available for this player")
                
                # Batting T20 Tab
                with tab2:
                    if not player_stats.get('batting_t20', pd.DataFrame()).empty:
                        df = player_stats['batting_t20']
                        st.subheader("T20 Batting Statistics")
                        
                        # Key metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            runs = df['runs_scored'].iloc[0] if 'runs_scored' in df.columns else "N/A"
                            st.metric("Total Runs", runs)
                        
                        with col2:
                            avg = df['batting_average'].iloc[0] if 'batting_average' in df.columns else "N/A"
                            st.metric("Batting Average", avg)
                        
                        with col3:
                            matches = df['matches_played'].iloc[0] if 'matches_played' in df.columns else "N/A"
                            st.metric("Matches", matches)
                        
                        with col4:
                            sr = df['batting_strike_rate'].iloc[0] if 'batting_strike_rate' in df.columns else "N/A"
                            st.metric("Strike Rate", sr)
                        
                        # More metrics
                        col5, col6, col7, col8 = st.columns(4)
                        
                        with col5:
                            hundreds = df['hundreds_scored'].iloc[0] if 'hundreds_scored' in df.columns else "N/A"
                            st.metric("Hundreds", hundreds)
                        
                        with col6:
                            fifties = df['scores_between_50_and_99'].iloc[0] if 'scores_between_50_and_99' in df.columns else "N/A"
                            st.metric("Fifties", fifties)
                        
                        with col7:
                            hs = df['highest_innings_score'].iloc[0] if 'highest_innings_score' in df.columns else "N/A"
                            st.metric("Highest Score", hs)
                        
                        with col8:
                            sixes = df['boundary_sixes'].iloc[0] if 'boundary_sixes' in df.columns else "N/A"
                            st.metric("Sixes", sixes)
                        
                        # Full table
                        st.markdown("### Complete Statistics")
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No T20 batting statistics available for this player")
                
                # Bowling ODI Tab
                with tab3:
                    if not player_stats.get('bowling_odi', pd.DataFrame()).empty:
                        df = player_stats['bowling_odi']
                        st.subheader("ODI Bowling Statistics")
                        
                        # Key metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            wickets = df['wickets_taken'].iloc[0] if 'wickets_taken' in df.columns else "N/A"
                            st.metric("Total Wickets", wickets)
                        
                        with col2:
                            avg = df['bowling_average'].iloc[0] if 'bowling_average' in df.columns else "N/A"
                            st.metric("Bowling Average", avg)
                        
                        with col3:
                            matches = df['matches_played'].iloc[0] if 'matches_played' in df.columns else "N/A"
                            st.metric("Matches", matches)
                        
                        with col4:
                            economy = df['economy_rate'].iloc[0] if 'economy_rate' in df.columns else "N/A"
                            st.metric("Economy Rate", economy)
                        
                        # More metrics
                        col5, col6, col7, col8 = st.columns(4)
                        
                        with col5:
                            sr = df['bowling_strike_rate'].iloc[0] if 'bowling_strike_rate' in df.columns else "N/A"
                            st.metric("Strike Rate", sr)
                        
                        with col6:
                            bbi = df['best_bowling_in_an_innings'].iloc[0] if 'best_bowling_in_an_innings' in df.columns else "N/A"
                            st.metric("Best Bowling", bbi)
                        
                        with col7:
                            four_wkts = df['four_wkts_exactly_in_an_inns'].iloc[0] if 'four_wkts_exactly_in_an_inns' in df.columns else "N/A"
                            st.metric("4 Wickets", four_wkts)
                        
                        with col8:
                            five_wkts = df['five_wickets_in_an_inns'].iloc[0] if 'five_wickets_in_an_inns' in df.columns else "N/A"
                            st.metric("5 Wickets", five_wkts)
                        
                        # Full table
                        st.markdown("### Complete Statistics")
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No ODI bowling statistics available for this player")
                
                # Bowling T20 Tab
                with tab4:
                    if not player_stats.get('bowling_t20', pd.DataFrame()).empty:
                        df = player_stats['bowling_t20']
                        st.subheader("T20 Bowling Statistics")
                        
                        # Key metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            wickets = df['wickets_taken'].iloc[0] if 'wickets_taken' in df.columns else "N/A"
                            st.metric("Total Wickets", wickets)
                        
                        with col2:
                            avg = df['bowling_average'].iloc[0] if 'bowling_average' in df.columns else "N/A"
                            st.metric("Bowling Average", avg)
                        
                        with col3:
                            matches = df['matches_played'].iloc[0] if 'matches_played' in df.columns else "N/A"
                            st.metric("Matches", matches)
                        
                        with col4:
                            economy = df['economy_rate'].iloc[0] if 'economy_rate' in df.columns else "N/A"
                            st.metric("Economy Rate", economy)
                        
                        # More metrics
                        col5, col6, col7, col8 = st.columns(4)
                        
                        with col5:
                            sr = df['bowling_strike_rate'].iloc[0] if 'bowling_strike_rate' in df.columns else "N/A"
                            st.metric("Strike Rate", sr)
                        
                        with col6:
                            bbi = df['best_bowling_in_an_innings'].iloc[0] if 'best_bowling_in_an_innings' in df.columns else "N/A"
                            st.metric("Best Bowling", bbi)
                        
                        with col7:
                            four_wkts = df['four_wkts_exactly_in_an_inns'].iloc[0] if 'four_wkts_exactly_in_an_inns' in df.columns else "N/A"
                            st.metric("4 Wickets", four_wkts)
                        
                        with col8:
                            five_wkts = df['five_wickets_in_an_inns'].iloc[0] if 'five_wickets_in_an_inns' in df.columns else "N/A"
                            st.metric("5 Wickets", five_wkts)
                        
                        # Full table
                        st.markdown("### Complete Statistics")
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No T20 bowling statistics available for this player")
    else:
        st.warning("No players found in database")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Cricket Stats Tracker**")
st.sidebar.markdown("Data from ESPN Cricinfo")
