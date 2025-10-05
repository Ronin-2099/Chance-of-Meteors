import requests
from datetime import datetime, timedelta

# API Key for NASA
API_KEY = "xbbp4akfa2CLalR3wKfnGGZPrh7uvwDowMRqAH7t"
BASE_URL = "https://api.nasa.gov/neo/rest/v1/feed"

def get_approaching_asteroids():
    """
    Fetches asteroids approaching in the next 7 days and prints them to the console.
    """
    # 1. Set the date range for the next 7 days
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "api_key": API_KEY
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"Error fetching data from NASA API: {err}")
        return

    data = response.json()
    all_asteroids = []

    # 2. Process the data from the 'feed' endpoint
    near_earth_objects = data.get("near_earth_objects", {})
    for date_str in near_earth_objects:
        for asteroid_data in near_earth_objects[date_str]:
            if not asteroid_data.get('close_approach_data'):
                continue

            all_asteroids.append({
                "id": asteroid_data["id"],
                "name": asteroid_data["name"],
                "is_hazardous": asteroid_data["is_potentially_hazardous_asteroid"],
                "diam_min": asteroid_data["estimated_diameter"]["meters"]["estimated_diameter_min"],
                "diam_max": asteroid_data["estimated_diameter"]["meters"]["estimated_diameter_max"],
                "approach_date": asteroid_data["close_approach_data"][0]["close_approach_date"]
            })

    # 3. Sort the list by approach date
    sorted_list = sorted(all_asteroids, key=lambda x: x["approach_date"])

    # 4. Print the formatted table
    print("\n☄️ Approaching Near-Earth Objects (Next 7 Days)\n")
    print("{:<12} {:<35} {:<25} {:<18} {:<15}".format(
        "ID", "Name", "Estimated Diameter (m)", "Approach Date", "Hazardous"
    ))
    print("-" * 115)
    
    if not sorted_list:
        print("No approaching asteroids found in the next 7 days.")
        return

    for a in sorted_list:
        hazardous_str = "Yes ⚠️" if a["is_hazardous"] else "No"
        diameter_str = f"{a['diam_min']:.2f} - {a['diam_max']:.2f}"
        print("{:<12} {:<35} {:<25} {:<18} {:<15}".format(
            a["id"], a["name"], diameter_str, a["approach_date"], hazardous_str
        ))

if __name__ == "__main__":
    get_approaching_asteroids()