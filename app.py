from flask import Flask, request, render_template
import requests
from datetime import datetime, timedelta
import math # Necesario para los cálculos

app = Flask(__name__)

API_KEY = "xbbp4akfa2CLalR3wKfnGGZPrh7uvwDowMRqAH7t" 
BASE_URL = "https://api.nasa.gov/neo/rest/v1/"

def calculate_deflection_dv(orbital_data):
    """
    Calcula el delta-v necesario para hacer segura la órbita de un asteroide.
    Modelo simplificado: aplica un impulso en el afelio para elevar el perihelio.
    """
    try:
        # Constantes físicas
        G = 6.67430e-11  # Constante gravitacional
        M_SUN = 1.989e30  # Masa del Sol en kg
        AU_TO_M = 149597870700  # UA en metros

        # Parámetros orbitales originales
        a_au = float(orbital_data['semi_major_axis'])
        e = float(orbital_data['eccentricity'])
        
        a_m = a_au * AU_TO_M # Eje semi-mayor en metros
        
        # Distancias originales en metros
        q_old_m = a_m * (1 - e) # Perihelio
        Q_old_m = a_m * (1 + e) # Afelio (este punto se mantiene)

        # Objetivo: elevar el perihelio a una distancia segura (afelio de la Tierra + 0.05 UA)
        TARGET_PERIHELION_AU = 1.017 + 0.05
        q_new_m = TARGET_PERIHELION_AU * AU_TO_M

        # Si el perihelio ya es seguro, no se necesita desvío
        if q_old_m >= q_new_m:
            return None

        # Usando la fórmula de la energía orbital (ecuación vis-viva)
        # v = sqrt(GM * (2/r - 1/a))
        
        # 1. Calcular velocidad en el afelio de la órbita original
        v_aphelion_old = math.sqrt(G * M_SUN * ((2 / Q_old_m) - (1 / a_m)))

        # 2. Calcular el nuevo eje semi-mayor para la órbita segura
        # Como Q se mantiene y q cambia, a_new = (Q_old + q_new) / 2
        a_new_m = (Q_old_m + q_new_m) / 2

        # 3. Calcular la nueva velocidad necesaria en el afelio
        v_aphelion_new = math.sqrt(G * M_SUN * ((2 / Q_old_m) - (1 / a_new_m)))

        # 4. El delta-v es la diferencia entre la velocidad nueva y la antigua
        delta_v = v_aphelion_new - v_aphelion_old
        
        # Nuevos parámetros orbitales para la visualización
        a_new_au = a_new_m / AU_TO_M
        e_new = (Q_old_m - q_new_m) / (Q_old_m + q_new_m)

        return {
            "required_dv_ms": delta_v,
            "target_perihelion_au": TARGET_PERIHELION_AU,
            "new_orbit_params": {
                "a": a_new_au,
                "e": e_new
            }
        }

    except (ValueError, KeyError, TypeError):
        # En caso de datos faltantes o incorrectos
        return None

@app.route("/", methods=["GET"])
def index():
    asteroid_id = request.args.get("asteroid_id")
    asteroid_data = None
    error = None
    deflection_data = None 

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

            if asteroid_data['is_potentially_hazardous_asteroid']:
                deflection_data = calculate_deflection_dv(orbital_data)

        except requests.exceptions.HTTPError:
            error = "Asteroid ID not found or API error."
        except (KeyError, IndexError, TypeError) as e:
            error = f"Missing or incorrectly formatted data in the API response: {e}"
        except Exception as err:
            error = f"An unexpected error occurred: {err}"
            
    return render_template("index.html", asteroid_data=asteroid_data, deflection_data=deflection_data, error=error)

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
    # Esta línea renderiza el simulador de impacto en el mapa
    return render_template("mapa.html")

@app.route("/sim")
def sim():
    original_params = {
        "name": request.args.get('name', 'Unknown Asteroid'),
        "hazardous": request.args.get('hazardous', 'false').lower() == 'true',
        "elements": {
            "a": request.args.get('sma', '0'),
            "e": request.args.get('ecc', '0'),
            "i": request.args.get('inc', '0'),
            "raan": request.args.get('raan', '0'),
            "omega": request.args.get('omega', '0'),
            "M": request.args.get('m', '0')
        }
    }

    deflection_data = None
    if original_params["hazardous"]:
        orbital_data_for_calc = {
            'semi_major_axis': original_params['elements']['a'],
            'eccentricity': original_params['elements']['e']
        }
        deflection_data = calculate_deflection_dv(orbital_data_for_calc)

    return render_template("sim.html", asteroid=original_params, deflection_data=deflection_data)

if __name__ == "__main__":
    app.run(debug=True)