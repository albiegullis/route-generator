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
    
    # 1. SET THE PROFILES AND STARTING POINT
    req_kwargs = {
        "format": "geojson",
        "elevation": True,
        "coordinates": [[lon, lat]]  # ONLY send the starting point!
    }

    # 2. THE SECRET ROUND-TRIP ALGORITHM
    route_options = {
        "round_trip": {
            "length": distance,
            "points": 5, # Tells the engine to generate a smooth circular loop
            "seed": 0    # (Optional) Randomize this to generate different loops later
        }
    }

    if terrain == 'road':
        req_kwargs["profile"] = 'wheelchair' # Paved only
    else:
        req_kwargs["profile"] = 'foot-hiking' # Trails and dirt
        # Force the engine to hunt for green spaces
        route_options["profile_params"] = {
            "weightings": {
                "green": 1,
                "quiet": 1
            }
        }
        
    req_kwargs["options"] = route_options

    print(f"Calculating {terrain} round trip for target: {distance}m...")
    
    try:
        route_data = client.directions(**req_kwargs)
        
        actual_distance = route_data['features'][0]['properties']['summary']['distance']
        print(f"Generated Route! Target: {distance}m, Actual: {actual_distance}m")
        
        return route_data
        
    except openrouteservice.exceptions.ApiError as e:
        if "Rate limit" in str(e) or "429" in str(e):
            raise HTTPException(status_code=429, detail="API rate limit reached. Please wait 60 seconds.")
        print(f"ORS API Error: {e}")
        raise HTTPException(status_code=400, detail="Could not generate a loop from this location.")
    except Exception as e:
        print(f"General Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))