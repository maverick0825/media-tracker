import streamlit as st
import requests

SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

def init_db():
    pass

def add_media(tmdb_id, title, media_type, release_date, poster_path, streaming_providers, watcher="Both", genres="", next_ep_info="", status="Want to Watch", notes=""):
    endpoint = f"{SUPABASE_URL}/rest/v1/media_items?on_conflict=tmdb_id"
    payload = {
        "tmdb_id": tmdb_id,
        "title": title,
        "media_type": media_type,
        "release_date": release_date,
        "poster_path": poster_path,
        "streaming_providers": streaming_providers,
        "watcher": watcher,
        "genres": genres,
        "next_ep_info": next_ep_info,
        "status": status,
        "notes": notes
    }
    try:
        res = requests.post(endpoint, headers=HEADERS, json=payload)
        if res.status_code not in (200, 201):
            st.error(f"Supabase write error ({res.status_code}): {res.text}")
    except Exception as e:
        st.error(f"Network error: {e}")

def get_watchlist(watcher_filter=None, status_filter=None, media_type_filter=None, genre_filter=None):
    params = ["select=*", "order=release_date.asc"]
    
    if watcher_filter and watcher_filter != "All":
        params.append(f"watcher=eq.{watcher_filter}")
    if status_filter and status_filter != "All":
        params.append(f"status=eq.{status_filter}")
    if media_type_filter and media_type_filter != "All":
        params.append(f"media_type=eq.{media_type_filter.lower()}")
    if genre_filter and genre_filter != "All":
        params.append(f"genres=ilike.*{genre_filter}*")
        
    query_str = "&".join(params)
    endpoint = f"{SUPABASE_URL}/rest/v1/media_items?{query_str}"
    
    try:
        res = requests.get(endpoint, headers=HEADERS)
        if res.status_code == 200:
            return res.json()
        st.error(f"Supabase fetch error ({res.status_code}): {res.text}")
        return []
    except Exception as e:
        st.error(f"Network error: {e}")
        return []

def update_status(tmdb_id, new_status):
    endpoint = f"{SUPABASE_URL}/rest/v1/media_items?tmdb_id=eq.{tmdb_id}"
    requests.patch(endpoint, headers=HEADERS, json={"status": new_status})

def update_watcher(tmdb_id, new_watcher):
    endpoint = f"{SUPABASE_URL}/rest/v1/media_items?tmdb_id=eq.{tmdb_id}"
    requests.patch(endpoint, headers=HEADERS, json={"watcher": new_watcher})

def delete_media(tmdb_id):
    endpoint = f"{SUPABASE_URL}/rest/v1/media_items?tmdb_id=eq.{tmdb_id}"
    requests.delete(endpoint, headers=HEADERS)
