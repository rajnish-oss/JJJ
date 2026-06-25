import requests
from dotenv import load_dotenv
import os
from urllib.parse import quote
import redis
from app.utils.generate_slug import generate_slug
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

load_dotenv()
apikey = os.getenv("location_iq")

def accurate_infrastructure(results):
    if not results:
        return None
 
    JUNK_TYPES = {
        'bus_stop', 'platform', 'stop_position', 'station_entrance', 
        'footway', 'residential', 'service', 'cycleway', 'path'
    }
    
    valid_candidates = []
    
    for place in results:
        place_class = place.get('class')
        place_type = place.get('type')
        importance = float(place.get('importance', 0))

        print("place class", place_class)
        print("place type", place_type)
        print("importance", importance)
        
    
        if place_type in JUNK_TYPES:
            continue

        weight = importance
        if place_class in {'amenity', 'building', 'landuse', 'office'}:
            weight += 0.5 
        elif place_class in {'highway', 'railway'} and place_type in {'motorway', 'trunk', 'primary', 'rail'}:
            weight += 0.2 
        else:
            continue 
            

        place['calculated_weight'] = weight
        valid_candidates.append(place)
        
    print("valid candidates", valid_candidates)

    if not valid_candidates:
        return None
    
        
    best_match = max(valid_candidates, key=lambda x: x['calculated_weight'])
    best_match.pop('calculated_weight', None)
    
    return best_match

def getLocationBoundary(address):
    if not apikey:
        raise ValueError("Missing LocationIQ API key. Set location_iq in your environment.")
    
    lowercase_query = address.lower()
    query = quote(lowercase_query, safe="")
    print(f"https://us1.locationiq.com/v1/search?key={apikey}&q={query}&format=json&=")
    
    res_obj = requests.get(f"https://us1.locationiq.com/v1/search?key={apikey}&q={query}&format=json&=")

    res_obj.raise_for_status()

    places = res_obj.json()
    print("places", places)
    # places = accurate_infrastructure(places)


    boundary = []

    if not places:
        return None
    
    for place in places:
        bounding_box = place.get("boundingbox")
        if not bounding_box or len(bounding_box) != 4:
            return None

        boundary.append(
                {
                    "south": float(bounding_box[0]),
                    "north": float(bounding_box[1]),
                    "west": float(bounding_box[2]),
                    "east": float(bounding_box[3]),
                },
        )
    
    boundaries = {
        "display_name": address,
        "boundary": boundary
    }
    return boundaries

def seed_infrastructure_to_redis(item):
    pipe = r.pipeline()
    asset_id = generate_slug(item["display_name"])
    
    # Store the master metadata document once
    meta_key = f"infrastructure:asset:{asset_id}"
    pipe.set(meta_key, json.dumps(item))
    
    # Index the center of EVERY bounding box in the array
    for index, b in enumerate(item["boundary"]):
        lat = (b["south"] + b["north"]) / 2
        lon = (b["west"] + b["east"]) / 2
        
        # Create a unique sub-key for the spatial index (e.g., "aiims-delhi_0")
        spatial_member_id = f"{asset_id}_{index}"
        
        # Remember: Redis expects (longitude, latitude, member)
        pipe.geoadd("infrastructure:geo_index", (lon, lat, spatial_member_id))
        
    pipe.execute()
    print(f"Successfully seeded {len(item['boundary'])} boundaries for {asset_id}!")
    return asset_id


def create_infrastructure_geofence(address):
    """Resolve an infrastructure address and seed its boundary into Redis."""
    boundaries = getLocationBoundary(address)
    if not boundaries:
        return None
    
    seed_infrastructure_to_redis(boundaries)



def check_user_geofence(user_lat, user_lon):
    # STEP 1: Find candidates within a 2km radius
    candidates = r.geosearch(
        "infrastructure:geo_index",
        longitude=user_lon,
        latitude=user_lat,
        radius=2000,
        unit="m"
    )
    
    if not candidates:
        print("No candidate found near this coordinate.")
        return None
    else:
        print(f"Found {len(candidates)} candidates near this coordinate.")
        
    processed_assets = set()
    
    # STEP 2: Exact containment verification
    for spatial_id in candidates:
        base_asset_id = spatial_id.rsplit('_', 1)[0]
        
        if base_asset_id in processed_assets:
            continue
        processed_assets.add(base_asset_id)
        
        asset_data_raw = r.get(f"infrastructure:asset:{base_asset_id}")
        
        # Defensive check: Ensure data is present and is not an empty/null string placeholder
        if not asset_data_raw or asset_data_raw in ("None", "null", ""):
            continue
            
        try:
            asset = json.loads(asset_data_raw)
        except json.JSONDecodeError as e:
            print(f"Skipping corrupted payload for key {base_asset_id}: {e}")
            continue
            
        boundaries = asset.get("boundary", [])
        
        for b in boundaries:
            # Check if bounding box coordinates exist to prevent KeyError
            if not all(k in b for k in ("south", "north", "west", "east")):
                continue
                
            # Exact containment bounding box algorithm
            if (b["south"] <= user_lat <= b["north"]) and (b["west"] <= user_lon <= b["east"]):
                return {
                    "asset_id": base_asset_id,
                    "display_name": asset.get("display_name", "Unknown Infrastructure")
                }
            
    return None