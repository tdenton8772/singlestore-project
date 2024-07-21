from flask import Flask, render_template, jsonify, request
import pymysql
import re
import threading
import time

app = Flask(__name__)

# SingleStore connection details
HOST = '127.0.0.1'
PORT = 3306
USER = 'root'
PASSWORD = 'password'
DATABASE = 'maritimedata'

# Function to call a stored procedure in SingleStore
def call_stored_procedure():
    connection = pymysql.connect(
        host=HOST,
        user=USER,
        port=PORT,
        password=PASSWORD,
        database=DATABASE
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("CALL StorePolyLine()")  # Replace with your stored procedure
            connection.commit()
    finally:
        connection.close()

# Background thread function to call the stored procedure every 5 seconds
def stored_procedure_thread():
    while True:
        call_stored_procedure()
        time.sleep(5)

# SingleStore query function
def query_singlestore(query, params=None):
    connection = pymysql.connect(
        host=HOST,
        user=USER,
        port=PORT,
        password=PASSWORD,
        database=DATABASE
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
    finally:
        connection.close()
    return results

# Parse LINESTRING format to list of coordinates
def parse_linestring(linestring):
    matches = re.findall(r'-?\d+\.\d+ -?\d+\.\d+', linestring)
    coordinates = [list(map(float, coord.split()))[::-1] for coord in matches]  # Reverse to [lat, lng]
    return coordinates

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    mmsi = request.args.get('mmsi')
    if mmsi:
        polyline_query = "SELECT GeoLine FROM ship_routes WHERE mmsi = %s"
        results = query_singlestore(polyline_query, (mmsi,))
    else:
        polyline_query = "SELECT GeoLine FROM ship_routes"
        results = query_singlestore(polyline_query)
    polylines = [parse_linestring(row[0]) for row in results]
    return jsonify(polylines)

@app.route('/metadata')
def metadata():
    maritime_count = query_singlestore("SELECT COUNT(*) FROM maritime_data")[0][0] if query_singlestore("SELECT COUNT(*) FROM maritime_data") else 0
    ship_routes_count = query_singlestore("SELECT COUNT(*) FROM ship_routes")[0][0] if query_singlestore("SELECT COUNT(*) FROM ship_routes") else 0
    mmsi_records = query_singlestore("SELECT DISTINCT mmsi FROM maritime_data")
    mmsi_list = [row[0] for row in mmsi_records] if mmsi_records else []
    return jsonify({
        "maritime_count": maritime_count,
        "ship_routes_count": ship_routes_count,
        "mmsi_list": mmsi_list
    })

@app.route('/long_mmsis')
def long_mmsis():
    print("LONG MMSI")
    long_mmsis_query = "SELECT DISTINCT mmsi FROM ship_routes WHERE GEOGRAPHY_LENGTH(GeoLine) > 100000"  # Adjust threshold as needed
    results = query_singlestore(long_mmsis_query)
    long_mmsis = [row[0] for row in results] if results else []
    return jsonify(long_mmsis)

@app.route('/anomalous_mmsis')
def anomalous_mmsis():
    # This is a placeholder for anomalous route detection logic
    # Adjust the query to match your criteria for anomalous routes
    anomalous_mmsis_query = "SELECT DISTINCT mmsi FROM ship_routes WHERE some_anomalous_condition"
    results = query_singlestore(anomalous_mmsis_query)
    anomalous_mmsis = [row[0] for row in results] if results else []
    return jsonify(anomalous_mmsis)

if __name__ == '__main__':
    # Start the background thread to call the stored procedure
    thread = threading.Thread(target=stored_procedure_thread)
    thread.daemon = True
    thread.start()

    # Run the Flask app
    app.run(debug=True)
