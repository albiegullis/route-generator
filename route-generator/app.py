from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import openrouteservice
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- API KEYS ---
API_KEY = os.environ.get("ORS_API_KEY")
client = openrouteservice.Client(key=API_KEY, retry_over_query_limit=False)

# --- ROUTE ENDPOINT ---
@app.get("/api/route")
def generate_route(distance: int = 5000, lat: float = 50.885, lon: float = -1.246, terrain: str = 'road'):
    
    req_kwargs = {
        "format": "geojson",
        "elevation": True,
        "coordinates": [[lon, lat]]  
    }

    # Setup profile conditions outside the loop
    if terrain == 'road':
        req_kwargs["profile"] = 'wheelchair'
        profile_params = None
    else:
        req_kwargs["profile"] = 'foot-hiking'
        profile_params = {
            "weightings": {
                "green": 1,
                "quiet": 1
            }
        }

    print(f"Calculating {terrain} round trip for target: {distance}m...")
    
    # We will adjust this target if the engine overshoots
    current_target = distance 
    best_route = None
    closest_diff = float('inf')

    try:
        # Give the engine 3 attempts to nail the distance
        for attempt in range(3):
            route_options = {
                "round_trip": {
                    "length": int(current_target),
                    "points": 5, 
                    "seed": 0    
                }
            }
            
            if profile_params:
                route_options["profile_params"] = profile_params
                
            req_kwargs["options"] = route_options
            
            # Fire the request
            route_data = client.directions(**req_kwargs)
            
            actual_distance = route_data['features'][0]['properties']['summary']['distance']
            diff = abs(actual_distance - distance)
            
            print(f"Attempt {attempt + 1}: Requested {int(current_target)}m -> Got {actual_distance}m")
            
            # Save the closest route we find
            if diff < closest_diff:
                closest_diff = diff
                best_route = route_data
                
            # If the distance is within 10% of the target, it's a success!
            if diff <= (distance * 0.10):
                print("Distance is within 10% tolerance. Nailed it!")
                return route_data
                
            # If it missed, calculate the ratio and adjust the target for the next attempt
            ratio = distance / actual_distance
            current_target = current_target * ratio
            
        print(f"Settling for closest attempt. Difference: {closest_diff}m")
        return best_route
        
    except openrouteservice.exceptions.ApiError as e:
        if "Rate limit" in str(e) or "429" in str(e):
            raise HTTPException(status_code=429, detail="API rate limit reached. Please wait 60 seconds.")
        print(f"ORS API Error: {e}")
        raise HTTPException(status_code=400, detail="Could not generate a loop from this location.")
    except Exception as e:
        print(f"General Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))