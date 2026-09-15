from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import openrouteservice
import math
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Your API key
API_KEY = os.environ.get("ORS_API_KEY")
client = openrouteservice.Client(key=API_KEY, retry_over_query_limit=False)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

@app.get("/api/route")
def generate_route(distance: int = 5000, lat: float = 50.885, lon: float = -1.246, terrain: str = 'road'):
    
    # THE TRANSLATOR: Map the user's choice to extreme ORS profiles
    if terrain == 'road':
        ors_profile = 'wheelchair' # Guarantees paved, smooth surfaces. Zero mud.
    else:
        ors_profile = 'foot-hiking' # Hunts for green spaces and dirt tracks.

    print(f"Calculating {ors_profile} route for target: {distance}m...")
    
    angle_sets = [
        [0, 60, 120, 180, 240, 300],    # Hexagon 1 (North/South aligned)
        [30, 90, 150, 210, 270, 330],   # Hexagon 2 (Offset by 30 degrees)
        [15, 75, 135, 195, 255, 315]    # Hexagon 3 (Offset by 15 degrees)
    ]
    
    for angles in angle_sets:
        current_target = distance * 0.75 
        best_route = None
        closest_diff = float('inf')
        
        try:
            for attempt in range(2):
                radius_m = current_target / (2 * math.pi)
                radius_deg = radius_m / 111320
                
                waypoints = []
                for angle_deg in angles:
                    angle_rad = math.radians(angle_deg)
                    point_lat = lat + (radius_deg * math.cos(angle_rad))
                    point_lon = lon + (radius_deg * math.sin(angle_rad)) / math.cos(math.radians(lat))
                    waypoints.append([point_lon, point_lat])
                    
                route_coords = [[lon, lat]] + waypoints + [[lon, lat]]
                
                # THE FIX: Use -1 (ORS code for "unlimited search radius")
                search_radiuses = [-1] * len(route_coords)
                
                route_data = client.directions(
                    route_coords, 
                    profile=ors_profile, # USING THE TRANSLATED PROFILE
                    format='geojson', 
                    elevation=True,
                    radiuses=search_radiuses
                )
                
                actual_distance = route_data['features'][0]['properties']['summary']['distance']
                diff = abs(actual_distance - distance)
                
                if diff < closest_diff:
                    closest_diff = diff
                    best_route = route_data
                    
                if diff <= 100:
                    print(f"Nailed it! Actual: {actual_distance}m")
                    return route_data
                    
                ratio = distance / actual_distance
                current_target = current_target * ratio
                
            print(f"Settling for closest attempt. Difference: {closest_diff}m")
            return best_route
            
        except openrouteservice.exceptions.ApiError as e:
            if "Rate limit" in str(e) or "429" in str(e):
                raise HTTPException(status_code=429, detail="API rate limit reached (40 per minute). Please wait 60 seconds and try again.")
            
            # THE SAFETY NET: Actually print the API error to the terminal!
            print(f"ORS API Error: {e}")
            continue 
        except Exception as e:
            print(f"General Error: {e}")
            continue 
            
    raise HTTPException(
        status_code=400, 
        detail="Cannot find a continuous path here. Try clicking further away from motorways or water."
    )