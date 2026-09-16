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

    # THE FIX 1: We use 'foot-walking' to guarantee pedestrian safety and pavements.
    if terrain == 'road':
        req_kwargs["profile"] = 'wheelchair'
        profile_params = None
    else:
        req_kwargs["profile"] = 'foot-walking'
        profile_params = {
            "weightings": {
                "green": 1,
                "quiet": 1
            }
        }

    print(f"Calculating {terrain} round trip for target: {distance}m...")
    
    current_target = distance 
    best_route = None
    closest_diff = float('inf')

    # Give the engine 3 attempts
    for attempt in range(3):
        try:
            route_options = {
                "round_trip": {
                    "length": int(current_target),
                    "points": 5, 
                    # THE FIX 2: Change the seed (direction) on every attempt!
                    "seed": attempt * 42 
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
            
            if diff < closest_diff:
                closest_diff = diff
                best_route = route_data
                
            if diff <= (distance * 0.10):
                print("Distance is within 10% tolerance. Nailed it!")
                return route_data
                
            ratio = distance / actual_distance
            current_target = current_target * ratio
            
        except openrouteservice.exceptions.ApiError as e:
            # If ORS hits a dead-end, catch it, print it, and let the loop try the next seed!
            print(f"Attempt {attempt + 1} Failed: Engine hit a dead end, rotating loop direction...")
            continue
        except Exception as e:
            print(f"General Error on Attempt {attempt + 1}: {e}")
            continue
            
    # After 3 attempts, return the best valid route we found
    if best_route:
        print(f"Settling for closest attempt. Difference: {closest_diff}m")
        return best_route
        
    # If all 3 seeds completely failed to find a path
    raise HTTPException(
        status_code=400, 
        detail="Cannot find a continuous loop from this location. Try clicking slightly closer to a main path."
    )