from flask import Flask, abort, jsonify, request, Response
import json
import requests
import time
import os
#from customException import ApplicationException
from cricket_parser_v2 import get_db_conn
app = Flask(__name__)
dbname = 'CRICKET_PERF'

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def index():
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'static', 'index.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return Response(html_content, mimetype='text/html')
    except Exception as e:
        return f'<h1>Error loading page</h1><p>{str(e)}</p>', 500
   
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'Resource not found'}), 404
    
@app.route('/api/v2/countries/all', methods=['GET'])
def get_all_countries():
    try:
        with get_db_conn(dbname) as sqlite_conn:
            cur = sqlite_conn.cursor()
            cur.execute('''select * from Countries; ''')
            
            col_names = [field[0] for field in cur.description]
            rows = cur.fetchall()
            
            result = []
            for row in rows:
                result.append(dict(zip(col_names, row)))
            
            return jsonify({'countries': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
@app.route('/api/v2/countries', methods=['GET'])
def get_country_players():
    query_parameters = request.args
    country_name = query_parameters.get('name')
    match_type = query_parameters.get('match_type')
    
    query = "select a.country_id,b.country,a.player_id,a.player,a.odi_cap,a.t20_cap from Players a join Countries b on a.country_id=b.country_id where"
    to_filter = []
    conditions = []

    if country_name:
        conditions.append('b.country=?')
        to_filter.append(country_name)
    if match_type:
        conditions.append('a.{}_cap=?'.format(match_type))
        to_filter.append('Y')
    
    if not conditions:
        return jsonify({'error': 'At least one filter parameter (name or match_type) is required'}), 400
    
    query += ' ' + ' AND '.join(conditions) + ';'
    
    try:
        with get_db_conn(dbname) as sqlite_conn:
            cur = sqlite_conn.cursor()
            cur.execute(query, to_filter)
            
            col_names = [field[0] for field in cur.description]
            rows = cur.fetchall()
            
            result = []
            for row in rows:
                result.append(dict(zip(col_names, row)))
            
            return jsonify({'players': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/v2/get_stats/countries', methods=['GET'])
def get_players_stats():
    query_parameters = request.args
    country_name = query_parameters.get('name')
    play_type = query_parameters.get('play_type')
    match_type = query_parameters.get('match_type')
    
    if not play_type or not match_type:
        return jsonify({'error': 'play_type and match_type are required'}), 400
    
    # Normalize match_type
    match_type_upper = match_type.upper()
    if match_type_upper == 'ODI':
        match_type_table = 'Odi'
    elif match_type_upper == 'T20':
        match_type_table = 'T20'
    else:
        return jsonify({'error': 'match_type must be ODI or T20'}), 400
    
    # Normalize play_type
    play_type_capitalized = play_type.capitalize()
    if play_type_capitalized not in ['Batting', 'Bowling']:
        return jsonify({'error': 'play_type must be Batting or Bowling'}), 400
    
    query = "select * from {}_Stats_{} where player in (select a.player from Players a join Countries b on a.country_id=b.country_id where".format(play_type_capitalized, match_type_table)
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
    
    if not conditions:
        return jsonify({'error': 'At least country name is required'}), 400
    
    query += ' ' + ' AND '.join(conditions) + ');'
    
    try:
        with get_db_conn(dbname) as sqlite_conn:
            cur = sqlite_conn.cursor()
            cur.execute(query, to_filter)
            
            col_names = [field[0] for field in cur.description]
            rows = cur.fetchall()
            
            result = []
            for row in rows:
                result.append(dict(zip(col_names, row)))
            
            return jsonify({'stats': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)