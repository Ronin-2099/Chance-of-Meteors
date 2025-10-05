from flask import Flask, request, render_template, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = "mifLhJbPOjAUcoXEcksajso2jdv5zq1TIQWENMHQ" 
BASE_URL = "https://api.nasa.gov/neo/rest/v1/"

@app.route("/", methods=["GET"])
def index():
    # (Esta función no necesita cambios)
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
                'orbital_period': round(float(orbital_data.get('orbital_period', 0))),
                'perihelion_distance': orbital_data.get('perihelion_distance', 'N/A'),
                'aphelion_distance': orbital_data.get('aphelion_distance', 'N/A')
            }
        except requests.exceptions.HTTPError:
            error = "ID de asteroide no encontrado o error en la API."
        except (KeyError, IndexError, TypeError) as e:
            error = f"Dato faltante o con formato incorrecto en la respuesta de la API: {e}"
        except Exception as err:
            error = f"Ocurrió un error inesperado: {err}"
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
        
        for date_str in data['near_earth_objects']:
            for asteroid in data['near_earth_objects'][date_str]:
                # --- SECCIÓN MODIFICADA ---
                # Extraemos la fecha de la primera aproximación futura
                approach_date = asteroid['close_approach_data'][0]['close_approach_date_full']
                
                asteroids_list.append({
                    'id': asteroid['id'],
                    'name': asteroid['name'],
                    'is_potentially_hazardous_asteroid': asteroid['is_potentially_hazardous_asteroid'],
                    'diameter_min': round(asteroid['estimated_diameter']['meters']['estimated_diameter_min'], 2),
                    'diameter_max': round(asteroid['estimated_diameter']['meters']['estimated_diameter_max'], 2),
                    'approach_date': approach_date # <-- Fecha añadida aquí
                })
        
        # Ordenamos por fecha de aproximación, no por nombre
        asteroids_list.sort(key=lambda x: x['approach_date'])
        # --- FIN DE LA SECCIÓN MODIFICADA ---

    except requests.exceptions.HTTPError:
        error = "No se pudo obtener la lista de asteroides de la API de NASA."
    except Exception as e:
        error = f"Ocurrió un error inesperado: {e}"
    
    return render_template("list.html", asteroids=asteroids_list, error=error)

@app.route("/mapa")
def mapa():
    return render_template("mapa.html")

@app.route("/elevation")
def get_elevation():
    return jsonify({"elevation": 1500.0})

if __name__ == "__main__":
    app.run(debug=True)