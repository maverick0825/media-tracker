from datetime import datetime, date, timedelta
import streamlit as st
import requests

TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

def search_content(query):
    url = f"{BASE_URL}/search/multi"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "include_adult": False,
        "language": "en-US",
        "page": 1
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []
        
    results = response.json().get("results", [])
    filtered = []
    
    for item in results:
        media_type = item.get("media_type")
        if media_type not in ["movie", "tv"]:
            continue
            
        tmdb_id = item.get("id")
        title = item.get("title") if media_type == "movie" else item.get("name")
        raw_release = item.get("release_date") if media_type == "movie" else item.get("first_air_date")
        release_date = raw_release if raw_release else "TBD"
        
        poster_path = f"{IMAGE_BASE_URL}{item.get('poster_path')}" if item.get("poster_path") else None
        overview = item.get("overview", "No synopsis available.")
        
        details = get_details(tmdb_id, media_type)
        genres = ", ".join([g["name"] for g in details.get("genres", [])])
        next_ep_info = ""
        
        if media_type == "tv":
            next_ep = details.get("next_episode_to_air")
            if next_ep:
                release_date = next_ep.get("air_date", release_date)
                ep_season = next_ep.get("season_number")
                ep_num = next_ep.get("episode_number")
                next_ep_info = f"S{ep_season}E{ep_num}: {next_ep.get('name', '')}"
            else:
                status = details.get("status", "")
                next_ep_info = f"Status: {status}"
                
        filtered.append({
            "tmdb_id": tmdb_id,
            "title": title,
            "media_type": media_type,
            "release_date": release_date,
            "poster_path": poster_path,
            "overview": overview,
            "genres": genres,
            "next_ep_info": next_ep_info
        })
        
    return filtered

def get_details(tmdb_id, media_type):
    url = f"{BASE_URL}/{media_type}/{tmdb_id}"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    res = requests.get(url, params=params)
    return res.json() if res.status_code == 200 else {}

def get_watch_providers(tmdb_id, media_type):
    url = f"{BASE_URL}/{media_type}/{tmdb_id}/watch/providers"
    params = {"api_key": TMDB_API_KEY}
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return "None listed"
    
    us_providers = res.json().get("results", {}).get("US", {})
    flatrate = us_providers.get("flatrate", [])
    names = [p["provider_name"] for p in flatrate]
    return ", ".join(names) if names else "Check streaming apps / Rental only"

def get_recommendations_for_user(seed_items):
    """Fetches recommendations based on up to 5 items currently in a user's list."""
    if not seed_items:
        return []
        
    seen_ids = {item["tmdb_id"] for item in seed_items}
    recommendations = []
    
    # Use the 5 most recent titles as recommendation seeds
    for item in seed_items[:5]:
        tmdb_id = item["tmdb_id"]
        media_type = item["media_type"]
        url = f"{BASE_URL}/{media_type}/{tmdb_id}/recommendations"
        params = {"api_key": TMDB_API_KEY, "language": "en-US", "page": 1}
        res = requests.get(url, params=params)
        
        if res.status_code == 200:
            for rec in res.json().get("results", [])[:3]:
                rec_id = rec.get("id")
                if rec_id in seen_ids:
                    continue
                seen_ids.add(rec_id)
                
                title = rec.get("title") if media_type == "movie" else rec.get("name")
                raw_rel = rec.get("release_date") if media_type == "movie" else rec.get("first_air_date")
                poster = f"{IMAGE_BASE_URL}{rec.get('poster_path')}" if rec.get("poster_path") else None
                
                recommendations.append({
                    "tmdb_id": rec_id,
                    "title": title,
                    "media_type": media_type,
                    "release_date": raw_rel if raw_rel else "TBD",
                    "poster_path": poster,
                    "overview": rec.get("overview", "No synopsis available."),
                    "recommended_because": item["title"]
                })
                
    return recommendations

def get_upcoming_media(media_type="movie"):
    """Fetches movies or TV shows dropping within the next 30 days."""
    today = date.today()
    future = today + timedelta(days=30)
    today_str = today.strftime("%Y-%m-%d")
    future_str = future.strftime("%Y-%m-%d")
    
    url = f"{BASE_URL}/discover/{media_type}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "include_adult": False,
        "page": 1
    }
    
    if media_type == "movie":
        params["primary_release_date.gte"] = today_str
        params["primary_release_date.lte"] = future_str
    else:
        params["air_date.gte"] = today_str
        params["air_date.lte"] = future_str
        
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return []
        
    results = res.json().get("results", [])
    upcoming = []
    
    for item in results[:12]:
        tmdb_id = item.get("id")
        title = item.get("title") if media_type == "movie" else item.get("name")
        raw_rel = item.get("release_date") if media_type == "movie" else item.get("first_air_date")
        poster = f"{IMAGE_BASE_URL}{item.get('poster_path')}" if item.get("poster_path") else None
        
        upcoming.append({
            "tmdb_id": tmdb_id,
            "title": title,
            "media_type": media_type,
            "release_date": raw_rel if raw_rel else "TBD",
            "poster_path": poster,
            "overview": item.get("overview", "No synopsis available.")
        })
        
    return upcoming
