# Cricket Stats Tracker

A clean, minimal web application for viewing cricket player statistics scraped from ESPN Cricinfo.

## Features

- View all countries in the database
- Search players by country and match type (ODI/T20)
- View detailed batting and bowling statistics

## Installation

1. Install Python dependencies:
```bash
pip3 install -r requirements.txt
```

## Running the Application

1. Start the Streamlit app:
```bash
streamlit run streamlit_app.py
```

2. The app will automatically open in your browser at:
```
http://localhost:8501
```

If it doesn't open automatically, navigate to the URL shown in the terminal.

## Usage

The Streamlit app has three main pages accessible via the sidebar:

1. **Countries** - View all countries in the database
2. **Players** - Search for players by country and match type
3. **Statistics** - View detailed batting or bowling statistics with summary metrics

## Database

The application uses SQLite database (`CRICKET_PERF.sqlite`) with the following tables:
- Countries
- Players
- Batting_Stats_Odi / Batting_Stats_T20
- Bowling_Stats_Odi / Bowling_Stats_T20

## Notes

- The database must be populated first using `cricket_parser_v2.py` if you want to scrape fresh data
- The existing database (`CRICKET_PERF.sqlite`) contains pre-scraped data
- The app uses Streamlit's default clean UI with data tables and interactive widgets
