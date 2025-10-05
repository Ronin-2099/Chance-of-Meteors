from flask import Flask, request, render_template, jsonify
import requests
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# Es mejor usar una clave de API única y válida.
API_KEY = "xbbp4akfa2CLalR3wKfnGGZPrh7uvwDowMRqAH7t" 
BASE_URL = "https://api.nasa.gov/neo/rest/v1/"

@app.route("/", methods=["GET"])
def index():
    asteroid_id = request.args.get("asteroid_id")
    asteroid_data = None
    error = None
    if asteroid_id:
        url = f"{BASE_URL}neo/{asteroid_id}?api_key={API_KEY}"
        try:
            response = requests.get(url)
            response.raise_for_status() 
            data = response.json()
            close_approach_info = data.get('close_approach_data', [{}])[0]
            orbital_data = data.get('orbital_data', {})
            
            asteroid_data = {
                'name': data.get('name'),
                'id': data.get('id'),
                'is_potentially_hazardous_asteroid': data.get('is_potentially_hazardous_asteroid'),
                'diameter_meters': {
                    'min': round(data.get('estimated_diameter', {}).get('meters', {}).get('estimated_diameter_min', 0), 2),
                    'max': round(data.get('estimated_diameter', {}).get('meters', {}).get('estimated_diameter_max', 0), 2)
                },
                'close_approach': {
                    'date': close_approach_info.get('close_approach_date_full', 'N/A'),
                    'velocity_kps': round(float(close_approach_info.get('relative_velocity', {}).get('kilometers_per_second', 0)), 2),
                    'miss_distance_km': round(float(close_approach_info.get('miss_distance', {}).get('kilometers', 0)), 2)
                },
                'semi_major_axis': orbital_data.get('semi_major_axis', 'N/A'),
                'eccentricity': orbital_data.get('eccentricity', 'N/A'),
                'inclination': orbital_data.get('inclination', 'N/A'),
                'ascending_node_longitude': orbital_data.get('ascending_node_longitude', 'N/A'),
                'perihelion_argument': orbital_data.get('perihelion_argument', 'N/A'),
                'mean_anomaly': orbital_data.get('mean_anomaly', 'N/A'),
                'orbital_period': round(float(orbital_data.get('orbital_period', 0))),
                'perihelion_distance': orbital_data.get('perihelion_distance', 'N/A'),
                'aphelion_distance': orbital_data.get('aphelion_distance', 'N/A')
            }
        except requests.exceptions.HTTPError:
            error = "Asteroid ID not found or API error."
        except (KeyError, IndexError, TypeError) as e:
            error = f"Missing or incorrectly formatted data in the API response: {e}"
        except Exception as err:
            error = f"An unexpected error occurred: {err}"
            
    return render_template("index.html", asteroid_data=asteroid_data, error=error)

@app.route("/list")
def list_asteroids():
    asteroids_list = []
    error = None
    try:
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        url = f"{BASE_URL}feed?start_date={start_date}&end_date={end_date}&api_key={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        temp_list = []
        for date_str in data.get('near_earth_objects', {}):
            for asteroid_data in data['near_earth_objects'][date_str]:
                temp_list.append({
                    'id': asteroid_data['id'],
                    'name': asteroid_data['name'],
                    'is_potentially_hazardous_asteroid': asteroid_data['is_potentially_hazardous_asteroid'],
                    'diameter_min': round(asteroid_data['estimated_diameter']['meters']['estimated_diameter_min'], 2),
                    'diameter_max': round(asteroid_data['estimated_diameter']['meters']['estimated_diameter_max'], 2),
                    'approach_date': asteroid_data['close_approach_data'][0]['close_approach_date_full']
                })
        asteroids_list = sorted(temp_list, key=lambda x: x['approach_date'])
    except requests.exceptions.HTTPError:
        error = "Could not retrieve the list of asteroids from the NASA API."
    except Exception as e:
        error = f"An unexpected error occurred: {e}"
    return render_template("list.html", asteroids=asteroids_list, error=error)

@app.route("/mapa")
def mapa():
    return render_template("mapa.html")

# --- RUTA /sim MODIFICADA ---
@app.route("/sim")
def sim():
    # Recolecta los parámetros orbitales de la URL
    orbital_params = {
        "name": request.args.get('name', 'Unknown Asteroid'),
        "hazardous": request.args.get('hazardous', 'false').lower() == 'true',
        "sma": request.args.get('sma', '0'),
        "ecc": request.args.get('ecc', '0'),
        "inc": request.args.get('inc', '0'),
        "raan": request.args.get('raan', '0'),
        "omega": request.args.get('omega', '0'),
        "m": request.args.get('m', '0')
    }
    # Pasa el diccionario de parámetros a la plantilla
    return render_template("sim.html", asteroid=orbital_params)

if __name__ == "__main__":
    app.run(debug=True)