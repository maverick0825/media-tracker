import requests
import streamlit as st

API_KEY = st.secrets["TMDB_API_KEY"]
BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w300"

GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
    10759: "Action & Adventure", 10762: "Kids", 10763: "News", 10764: "Reality",
    10765: "Sci-Fi & Fantasy", 10766: "Soap", 10767: "Talk", 10768: "War & Politics"
}

def get_tv_details(tmdb_id):
    """Fetches series details, specifically next_episode_to_air."""
    url = f"{BASE_URL}/tv/{tmdb_id}"
    params = {"api_key": API_KEY, "language": "en-US"}
    try:
        data = requests.get(url, params=params).json()
        next_ep = data.get("next_episode_to_air")
        status = data.get("status", "")
        
        if next_ep:
            return {
                "next_air_date": next_ep.get("air_date"),
                "next_ep_tag": f"S{next_ep.get('season_number')}E{next_ep.get('episode_number')}",
                "next_ep_name": next_ep.get("name", "")
            }
        elif status in ["Ended", "Canceled"]:
            return {"status_note": "Series Ended"}
        else:
            return {"status_note": "Awaiting Next Season"}
    except Exception:
        return {}

def search_content(query):
    if not query:
        return []
    url = f"{BASE_URL}/search/multi"
    params = {
        "api_key": API_KEY,
        "query": query,
        "include_adult": "false",
        "language": "en-US"
    }
    response = requests.get(url, params=params).json()
    results = []
    
    for item in response.get("results", []):
        media_type = item.get("media_type")
        if media_type not in ["movie", "tv"]:
            continue
            
        title = item.get("title") if media_type == "movie" else item.get("name")
        poster = f"{IMG_BASE}{item['poster_path']}" if item.get("poster_path") else None
        
        genre_ids = item.get("genre_ids", [])
        genre_names = [GENRE_MAP.get(gid) for gid in genre_ids if gid in GENRE_MAP]
        
        # If it's a TV show, check for upcoming episodes
        next_ep_info = ""
        release_date = item.get("release_date") if media_type == "movie" else item.get("first_air_date")
        
        if media_type == "tv":
            details = get_tv_details(item["id"])
            if "next_air_date" in details:
                release_date = details["next_air_date"]
                next_ep_info = f"{details['next_ep_tag']}: {details['next_ep_name']}"
            elif "status_note" in details:
                next_ep_info = details["status_note"]
        
        results.append({
            "tmdb_id": item["id"],
            "title": title,
            "media_type": media_type,
            "release_date": release_date or "TBD",
            "poster_path": poster,
            "genres": ", ".join(genre_names),
            "overview": item.get("overview", ""),
            "next_ep_info": next_ep_info
        })
    return results

def get_watch_providers(tmdb_id, media_type, region="US"):
    url = f"{BASE_URL}/{media_type}/{tmdb_id}/watch/providers"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params).json()
    
    results = response.get("results", {}).get(region, {})
    flatrate = results.get("flatrate", [])
    
    providers = [p.get("provider_name") for p in flatrate]
    return ", ".join(providers) if providers else "Not currently streaming"
