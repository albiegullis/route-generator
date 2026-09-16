from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import openrouteservice
import google.generativeai as genai  # Added import
import math
import os
import json                          # Added import

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- API KEYS ---
API_KEY = os.environ.get("ORS_API_KEY")
client = openrouteservice.Client(key=API_KEY, retry_over_query_limit=False)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ai_model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-3.6-flash')

# --- THE AI SURGEON FUNCTION ---
def clean_route_with_ai(route_geojson, target_distance_meters: int):
    """
    Sends the route coordinates to Gemini to trim unnecessary out-and-back spurs
    and GPS artifacts while preserving the total distance.
    """
    if not ai_model or not route_geojson:
        return route_geojson

    try:
        raw_coords = route_geojson['features'][0]['geometry']['coordinates']
        
        prompt = f"""
        You are an expert running route optimization AI.
        Below is a GeoJSON array of [longitude, latitude] or [longitude, latitude, elevation] coordinates.
        The user wants a loop run targeting {target_distance_meters} meters.

        Your job:
        1. Identify any "out-and-back" spurs (where the path runs down a dead-end road and immediately turns 180 degrees back).
        2. Identify and smooth out unnatural sharp spikes or zig-zags caused by rigid waypoint snapping.
        3. Remove those unnecessary spurs while keeping the loop continuous.
        4. CRITICAL: Keep the overall path connected and maintain a total distance as close to {target_distance_meters} meters as possible.

        Return ONLY a valid JSON array of coordinates, e.g. [[lon, lat], [lon, lat], ...].
        Do not include markdown fences, backticks, or explanatory text.

        Raw Coordinates:
        {json.dumps(raw_coords)}
        """

        response = ai_model.generate_content(prompt)
        text = response.text.strip()

        # Strip accidental markdown code fences if Gemini outputs them
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        cleaned_coords = json.loads(text)

        if isinstance(cleaned_coords, list) and len(cleaned_coords) > 2:
            route_geojson['features'][0]['geometry']['coordinates'] = cleaned_coords
            print("Gemini successfully polished the route.")
            
        return route_geojson

    except Exception as e:
        # Failsafe: if the AI call fails or hallucinates invalid JSON, return the raw ORS route
        print(f"AI surgery failed, falling back to original route: {e}")
        return route_geojson


# --- ROUTE ENDPOINT ---
@app.get("/api/route")
def generate_route(distance: int = 5000, lat: float = 50.885, lon: float = -1.246, terrain: str = 'road'):
    
    # 1. SET THE PROFILES AND ADVANCED OPTIONS
    req_kwargs = {
        "format": "geojson",
        "elevation": True
    }

    if terrain == 'road':
        req_kwargs["profile"] = 'wheelchair' # Guarantees paved, step-free surfaces
        # No extra options needed; we just want smooth pavement
    else:
        req_kwargs["profile"] = 'foot-hiking' # Trails and dirt paths
        # THE MAGIC TRICK: Force the engine to hunt for nature and avoid cars
        req_kwargs["options"] = {
            "profile_params": {
                "weightings": {
                    "green": 1,
                    "quiet": 1
                }
            }
        }

    print(f"Calculating {terrain} route for target: {distance}m...")
    
    angle_sets = [
        [0, 60, 120, 180, 240, 300],    # Hexagon 1
        [30, 90, 150, 210, 270, 330],   # Hexagon 2
        [15, 75, 135, 195, 255, 315]    # Hexagon 3
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
                
                # Add our dynamic coordinates and search radiuses to the request arguments
                req_kwargs["coordinates"] = route_coords
                req_kwargs["radiuses"] = [-1] * len(route_coords)
                
                # 2. FIRE THE REQUEST WITH THE NEW OPTIONS
                route_data = client.directions(**req_kwargs)
                
                actual_distance = route_data['features'][0]['properties']['summary']['distance']
                diff = abs(actual_distance - distance)
                
                if diff < closest_diff:
                    closest_diff = diff
                    best_route = route_data
                    
                if diff <= 100:
                    print(f"Nailed it! Actual: {actual_distance}m")
                    return clean_route_with_ai(route_data, distance)
                    
                ratio = distance / actual_distance
                current_target = current_target * ratio
                
            print(f"Settling for closest attempt. Difference: {closest_diff}m")
            return clean_route_with_ai(best_route, distance)
            
        except openrouteservice.exceptions.ApiError as e:
            if "Rate limit" in str(e) or "429" in str(e):
                raise HTTPException(status_code=429, detail="API rate limit reached. Please wait 60 seconds and try again.")
            print(f"ORS API Error: {e}")
            continue 
        except Exception as e:
            print(f"General Error: {e}")
            continue 
            
    raise HTTPException(
        status_code=400, 
        detail="Cannot find a continuous path here. Try clicking further away from motorways or water."
    )