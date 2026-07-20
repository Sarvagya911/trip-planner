import asyncio, os
from dotenv import load_dotenv
load_dotenv()
import httpx
from app.services.geocoding import get_geocoding_service

async def main():
    lon, lat = await get_geocoding_service().geocode("Madikeri")
    print("coords lat,lon:", lat, lon)
    key = os.environ["FOURSQUARE_API_KEY"]
    resp = httpx.get(
        "https://places-api.foursquare.com/places/search",
        params={
            "ll": f"{lat},{lon}",
            "radius": 8000,
            "fsq_category_ids": "4bf58dd8d48988d1fa931735",
            "limit": 20,
            "sort": "RATING",
            "fields": "name,rating,location,latitude,longitude",
        },
        headers={
            "Authorization": f"Bearer {key}",
            "X-Places-Api-Version": "2025-06-17",
            "accept": "application/json",
        },
        timeout=20,
    )
    print("STATUS:", resp.status_code)
    print("BODY:", resp.text[:600])

asyncio.run(main())