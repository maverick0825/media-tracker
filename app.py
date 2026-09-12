from datetime import datetime, date
import streamlit as st
import database as db
import tmdb

st.set_page_config(page_title="Team TK's Watch Lists", layout="wide", initial_sidebar_state="collapsed")
db.init_db()

def get_tmdb_url(tmdb_id, media_type="movie"):
    return f"https://www.themoviedb.org/{media_type}/{tmdb_id}"

def render_countdown(release_date_str, media_type="movie", next_ep_info=""):
    prefix = "📺 Next Ep" if media_type == "tv" else "🎬 Release"
    
    if not release_date_str or release_date_str == "TBD":
        return f"{prefix}: Date TBD"
        
    try:
        rel_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
        today = date.today()
        days_left = (rel_date - today).days
        formatted_date = rel_date.strftime('%a, %b %d')
        ep_label = f" ({next_ep_info})" if next_ep_info and ":" in next_ep_info else ""
        
        if days_left > 1:
            return f"⏳ **{prefix} in {days_left} days** — {formatted_date}{ep_label}"
        elif days_left == 1:
            return f"🔥 **{prefix} tomorrow!** — {formatted_date}{ep_label}"
        elif days_left == 0:
            return f"🎉 **{prefix} drops TODAY!**{ep_label}"
        else:
            if media_type == "tv" and next_ep_info:
                return f"ℹ️ {next_ep_info}"
            return f"✅ Released ({formatted_date})"
    except Exception:
        return f"📅 {release_date_str}"

st.title("🎬 Team TK's Watch Lists")

menu = st.sidebar.radio("Navigate", [
    "Our Watchlists", 
    "Search & Add", 
    "✨ Recommendations", 
    "📅 Coming Soon (Next 30 Days)"
])

ALL_GENRES = [
    "All", "Action", "Adventure", "Animation", "Comedy", "Crime", 
    "Documentary", "Drama", "Family", "Fantasy", "Horror", "Mystery", 
    "Romance", "Sci-Fi", "Thriller"
]

if menu == "Search & Add":
    st.subheader("🔍 Search Titles")
    search_term = st.text_input("Enter title...", placeholder="e.g. Reacher, Severance, Dune")
    
    if search_term:
        results = tmdb.search_content(search_term)
        if not results:
            st.info("No titles found.")
        
        for item in results:
            with st.container(border=True):
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    if item["poster_path"]:
                        st.image(item["poster_path"], width=160)
                    else:
                        st.write("🖼️ *No poster*")
                
                with col2:
                    link = get_tmdb_url(item["tmdb_id"], item["media_type"])
                    st.markdown(f"### [{item['title']}]({link}) ({item['media_type'].upper()})")
                    st.markdown(render_countdown(item["release_date"], item["media_type"], item.get("next_ep_info", "")))
                    if item["genres"]:
                        st.caption(f"**Genres:** {item['genres']}")
                    st.caption(item["overview"])
                    
                    add_col1, add_col2 = st.columns([1, 1])
                    with add_col1:
                        target_list = st.selectbox(
                            "Add to list:", 
                            ["Both", "TJ", "Kristen"], 
                            key=f"target_{item['tmdb_id']}"
                        )
                    with add_col2:
                        st.write("")
                        st.write("")
                        if st.button("➕ Add to Registry", key=f"add_{item['tmdb_id']}", width="stretch"):
                            providers = tmdb.get_watch_providers(item["tmdb_id"], item["media_type"])
                            db.add_media(
                                tmdb_id=item["tmdb_id"],
                                title=item["title"],
                                media_type=item["media_type"],
                                release_date=item["release_date"],
                                poster_path=item["poster_path"],
                                streaming_providers=providers,
                                watcher=target_list,
                                genres=item["genres"],
                                next_ep_info=item.get("next_ep_info", ""),
                                status="Want to Watch"
                            )
                            st.success(f"Added to {target_list}'s List!")
                            st.rerun()

elif menu == "Our Watchlists":
    active_tab = st.radio(
        "Select Watchlist View:", 
        ["Both Watching", "TJ's Watch List", "Kristen's Watch List", "View All Items"],
        horizontal=True
    )
    
    watcher_map = {
        "Both Watching": "Both",
        "TJ's Watch List": "TJ",
        "Kristen's Watch List": "Kristen",
        "View All Items": "All"
    }
    selected_watcher = watcher_map[active_tab]
    
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        status_filter = st.selectbox("Status", ["All", "Want to Watch", "Watching", "Watched"])
    with f_col2:
        type_filter = st.selectbox("Type", ["All", "Movie", "TV"])
    with f_col3:
        genre_filter = st.selectbox("Genre", ALL_GENRES)
        
    items = db.get_watchlist(
        watcher_filter=selected_watcher, 
        status_filter=status_filter, 
        media_type_filter=type_filter,
        genre_filter=genre_filter
    )
    
    if not items:
        st.write("No items found matching the current filters.")
    else:
        st.caption(f"Showing {len(items)} item(s)")
        
        cols = st.columns(2)
        for idx, row in enumerate(items):
            with cols[idx % 2]:
                with st.container(border=True):
                    card_col1, card_col2 = st.columns([1, 2])
                    with card_col1:
                        if row["poster_path"]:
                            st.image(row["poster_path"], width=170)
                    with card_col2:
                        link = get_tmdb_url(row["tmdb_id"], row["media_type"])
                        st.markdown(f"### [{row['title']}]({link})")
                        st.caption(render_countdown(row["release_date"], row["media_type"], row.get("next_ep_info", "")))
                        if row["genres"]:
                            st.caption(f"🏷️ `{row['genres']}`")
                        st.markdown(f"📺 **Streaming:** `{row['streaming_providers']}`")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        new_status = st.selectbox(
                            "Status", 
                            ["Want to Watch", "Watching", "Watched"], 
                            index=["Want to Watch", "Watching", "Watched"].index(row["status"]),
                            key=f"status_{row['tmdb_id']}"
                        )
                        if new_status != row["status"]:
                            db.update_status(row["tmdb_id"], new_status)
                            st.rerun()
                    with c2:
                        new_watcher = st.selectbox(
                            "List", 
                            ["Both", "TJ", "Kristen"], 
                            index=["Both", "TJ", "Kristen"].index(row["watcher"]),
                            key=f"watcher_{row['tmdb_id']}"
                        )
                        if new_watcher != row["watcher"]:
                            db.update_watcher(row["tmdb_id"], new_watcher)
                            st.rerun()
                            
                    if st.button("🗑️ Remove", key=f"del_{row['tmdb_id']}", type="secondary", width="stretch"):
                        db.delete_media(row["tmdb_id"])
                        st.rerun()

elif menu == "✨ Recommendations":
    st.subheader("✨ Recommended For You")
    
    rec_target = st.radio(
        "Generate recommendations based on list:",
        ["Both", "TJ", "Kristen"],
        horizontal=True
    )
    
    user_items = db.get_watchlist(watcher_filter=rec_target)
    
    if not user_items:
        st.info(f"No saved items found for '{rec_target}' yet. Add a few titles to unlock recommendations!")
    else:
        with st.spinner("Finding recommendations based on your tastes..."):
            recs = tmdb.get_recommendations_for_user(user_items)
            
        if not recs:
            st.write("No direct recommendations found yet. Try adding a couple more titles.")
        else:
            cols = st.columns(2)
            for idx, item in enumerate(recs):
                with cols[idx % 2]:
                    with st.container(border=True):
                        card_col1, card_col2 = st.columns([1, 2])
                        with card_col1:
                            if item["poster_path"]:
                                st.image(item["poster_path"], width=170)
                        with card_col2:
                            link = get_tmdb_url(item["tmdb_id"], item["media_type"])
                            st.markdown(f"### [{item['title']}]({link}) ({item['media_type'].upper()})")
                            st.caption(f"💡 *Because you have '{item['recommended_because']}' in your list*")
                            st.write(item["overview"])
                        
                        target_list = st.selectbox(
                            "Add to list:", 
                            ["Both", "TJ", "Kristen"], 
                            index=["Both", "TJ", "Kristen"].index(rec_target),
                            key=f"rec_target_{item['tmdb_id']}"
                        )
                        
                        if st.button("➕ Add to Registry", key=f"add_rec_{item['tmdb_id']}", width="stretch"):
                            details = tmdb.get_details(item["tmdb_id"], item["media_type"])
                            genres = ", ".join([g["name"] for g in details.get("genres", [])])
                            providers = tmdb.get_watch_providers(item["tmdb_id"], item["media_type"])
                            
                            db.add_media(
                                tmdb_id=item["tmdb_id"],
                                title=item["title"],
                                media_type=item["media_type"],
                                release_date=item["release_date"],
                                poster_path=item["poster_path"],
                                streaming_providers=providers,
                                watcher=target_list,
                                genres=genres,
                                next_ep_info="",
                                status="Want to Watch"
                            )
                            st.success(f"Added to {target_list}'s List!")
                            st.rerun()

elif menu == "📅 Coming Soon (Next 30 Days)":
    st.subheader("📅 Releasing in the Next 30 Days")
    
    media_choice = st.selectbox("Select Media Type:", ["Movies", "TV Shows"])
    type_code = "movie" if media_choice == "Movies" else "tv"
    
    with st.spinner(f"Loading upcoming {media_choice.lower()}..."):
        upcoming_items = tmdb.get_upcoming_media(type_code)
        
    if not upcoming_items:
        st.info("No upcoming releases found in this window.")
    else:
        cols = st.columns(2)
        for idx, item in enumerate(upcoming_items):
            with cols[idx % 2]:
                with st.container(border=True):
                    card_col1, card_col2 = st.columns([1, 2])
                    with card_col1:
                        if item["poster_path"]:
                            st.image(item["poster_path"], width=170)
                    with card_col2:
                        link = get_tmdb_url(item["tmdb_id"], item["media_type"])
                        st.markdown(f"### [{item['title']}]({link})")
                        st.markdown(render_countdown(item["release_date"], item["media_type"]))
                        st.caption(item["overview"])
                    
                    target_list = st.selectbox(
                        "Add to list:", 
                        ["Both", "TJ", "Kristen"], 
                        key=f"cs_target_{item['tmdb_id']}"
                    )
                    if st.button("➕ Add to Registry", key=f"add_cs_{item['tmdb_id']}", width="stretch"):
                        details = tmdb.get_details(item["tmdb_id"], item["media_type"])
                        genres = ", ".join([g["name"] for g in details.get("genres", [])])
                        providers = tmdb.get_watch_providers(item["tmdb_id"], item["media_type"])
                        
                        db.add_media(
                            tmdb_id=item["tmdb_id"],
                            title=item["title"],
                            media_type=item["media_type"],
                            release_date=item["release_date"],
                            poster_path=item["poster_path"],
                            streaming_providers=providers,
                            watcher=target_list,
                            genres=genres,
                            next_ep_info="",
                            status="Want to Watch"
                        )
                        st.success(f"Added to {target_list}'s List!")
                        st.rerun()
