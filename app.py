import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
import numpy as np
import plotly.graph_objects as go

# --- CHALLENGE SETTINGS ---
API_KEY = "7ze79tPyTI9tSw79kXEmtuIdL0c2vwspke2TJVm7"
FEED_URL = "https://api.nasa.gov/neo/rest/v1/feed"
LOOKUP_BASE_URL = "https://api.nasa.gov/neo/rest/v1/neo/"
APOD_URL = "https://api.nasa.gov/planetary/apod"
DENSITY_KG_M3 = 3000  # Typical asteroid density (kg/m³)

TEAM_NAME = "Asteroid Clash"
PARTICIPANTS = "Heitor Collyer Lebid and Aline Collyer Lebid"
CITY = "Santos-SP"
CHALLENGE_TITLE = "🚀 NASA 2025 Space Challenge!"

# --- FUNCTION TO GET APOD IMAGE ---
@st.cache_data(ttl=3600 * 24)
def get_apod_data(api_key, query_date=None):
    apod_url = f"{APOD_URL}?api_key={api_key}"
    if query_date:
        apod_url += f"&date={query_date}"
    try:
        response = requests.get(apod_url)
        response.raise_for_status()
        data = response.json()
        return data.get('hdurl', data.get('url')), data.get('title', ''), data.get('explanation', '')
    except requests.exceptions.RequestException:
        return None, None, None

# --- STYLE SETTINGS ---
st.set_page_config(page_title="NEO Tracker Kids", layout="wide")
st.markdown("""
<style>
.stAlert {background-color: #f75d59;}
h1 {color: #f75d59;}
.stButton>button {
    background-color: #007bff;
    color: white;
    border-radius: 12px;
}
.header-container {
    background: linear-gradient(135deg, #1a237e, #283593, #3949ab);
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 20px;
    color: white;
    text-align: center;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
}
.challenge-title {
    font-size: 2.8rem;
    font-weight: bold;
    color: #ffd700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
}
.team-name {
    font-size: 3.8rem;
    font-weight: 900;
    color: #00ff7f;
    font-style: italic;
    text-shadow: 3px 3px 6px rgba(0,0,0,0.6);
}
.participants {
    font-size: 1.2rem;
    color: #ffffff;
    background-color: rgba(255,255,255,0.2);
    padding: 10px;
    border-radius: 8px;
    display: inline-block;
    font-weight: bold;
}
.participants span {
    color: #ffeb3b;
    font-size: 1.4rem;
}
.game-badge {
    display: inline-block;
    background: #ff5722;
    padding: 6px 12px;
    border-radius: 12px;
    font-weight: bold;
    font-size: 1.2rem;
    color: white;
    animation: glow 2s infinite alternate;
}
@keyframes glow {
    from { box-shadow: 0 0 5px #ff5722; }
    to { box-shadow: 0 0 20px #ffccbc; }
}
.explanation {
    font-size: 1.1rem;
    color: #444;
}
.footer {
    font-size: 0.9rem;
    color: #888;
    padding: 20px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown(f"""
<div class="header-container">
    <div class="challenge-title">{CHALLENGE_TITLE}</div>
    <div class="team-name">Team: {TEAM_NAME}</div>
    <div class="participants">
        Participants: <span>{PARTICIPANTS}</span> | City: {CITY}
    </div>
    <div class="game-badge">🎮 Challenge Active!</div>
</div>
""", unsafe_allow_html=True)

# --- INTRODUCTION ---
st.markdown("""
<div class="explanation">
👋 Hello, Young Space Explorer! 🚀<br>
This app shows real asteroid data provided by NASA APIs.<br>
You can explore the asteroids near Earth and even simulate deflection missions!<br>
Let’s learn and play together! 🌍💫
</div>
""", unsafe_allow_html=True)

# --- IMPROVED DATE RANGE SELECTION ---
st.title("🛰️ Asteroid Tracking")
st.markdown("""
<div class="explanation">
🗓 <b>Select a date range (maximum of 7 days)</b><br>
to discover which <i>potentially hazardous asteroids</i> are approaching Earth.<br>
Explore real NASA data and learn about the objects that travel near our planet! 🌍✨
</div>
""", unsafe_allow_html=True)

today = date.today()
default_start = today
default_end = today + timedelta(days=2)

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    start_date_input = st.date_input("Start Date", default_start)
with col2:
    end_date_input = st.date_input("End Date", default_end)
with col3:
    st.markdown("##")
    if st.button("Search Asteroids"):
        delta = (end_date_input - start_date_input).days
        if delta < 0 or delta > 7:
            st.error("🚨 Invalid date range! Please select up to 7 days only.")
            st.session_state['run_analysis'] = False
        else:
            st.session_state['start_date'] = start_date_input.strftime("%Y-%m-%d")
            st.session_state['end_date'] = end_date_input.strftime("%Y-%m-%d")
            st.session_state['run_analysis'] = True
            st.cache_data.clear()

# --- CALCULATION FUNCTIONS ---
def calculate_impact_energy(diameter_km, velocity_km_s):
    diameter_m = diameter_km * 1000
    volume_m3 = (1/6) * np.pi * (diameter_m ** 3)
    mass_kg = volume_m3 * DENSITY_KG_M3
    velocity_m_s = velocity_km_s * 1000
    kinetic_energy_joule = 0.5 * mass_kg * (velocity_m_s ** 2)
    megatons_tnt = kinetic_energy_joule / (4.184e15)
    return megatons_tnt

def estimate_crater_size(megatons_tnt):
    if megatons_tnt <= 0:
        return 0, 0
    crater_diameter_km = 0.016 * (megatons_tnt ** (1/3))
    return crater_diameter_km, megatons_tnt

@st.cache_data(ttl=3600)
def get_hazardous_asteroid_details(start_date_str, end_date_str):
    feed_url_completa = f"{FEED_URL}?start_date={start_date_str}&end_date={end_date_str}&api_key={API_KEY}"
    try:
        feed_response = requests.get(feed_url_completa)
        feed_response.raise_for_status()
        feed_data = feed_response.json()
        near_earth_objects = feed_data.get('near_earth_objects', {})
        hazardous_ids = []
        for asteroid_list in near_earth_objects.values():
            for asteroid in asteroid_list:
                if asteroid.get('is_potentially_hazardous_asteroid'):
                    hazardous_ids.append(asteroid.get('id'))
        if not hazardous_ids:
            return None, 0
    except Exception:
        return None, 0

    asteroids_complete = []
    for neo_id in hazardous_ids:
        lookup_url_completa = f"{LOOKUP_BASE_URL}{neo_id}?api_key={API_KEY}"
        try:
            lookup_response = requests.get(lookup_url_completa)
            lookup_response.raise_for_status()
            full_info = lookup_response.json()

            orbit = full_info.get('orbital_data', {})
            close_approach_data = full_info.get('close_approach_data', [{}])[0]
            name = full_info.get('name', 'N/A')
            diam_max_km = full_info['estimated_diameter']['kilometers']['estimated_diameter_max']
            velocity_km_s = float(close_approach_data['relative_velocity']['kilometers_per_second'])

            megatons_tnt = calculate_impact_energy(diam_max_km, velocity_km_s)
            crater_diam, _ = estimate_crater_size(megatons_tnt)

            asteroids_complete.append({
                "Name": name,
                "Close Approach Date": close_approach_data.get('close_approach_date_full', 'N/A').split()[0],
                "Danger": "YES",
                "Diameter (km)": f"{diam_max_km:.3f}",
                "Velocity (km/s)": f"{velocity_km_s:.2f}",
                "Energy (Mt TNT)": f"{megatons_tnt:.2f}",
                "Crater Diameter (km)": f"{crater_diam:.2f}",
                "Lunar Distance": f"{float(close_approach_data['miss_distance']['lunar']):.2f}",
                "Orbital Period (days)": f"{float(orbit.get('orbital_period')):,.2f}",
                "Eccentricity": orbit.get('eccentricity', 'N/A'),
                "Inclination (°)": orbit.get('inclination', 'N/A'),
                "Orbit Type": orbit.get('orbit_class', {}).get('orbit_class_type', 'N/A'),
                "Orbit Description": orbit.get('orbit_class', {}).get('orbit_class_description', 'N/A'),
                "JPL Link": f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={neo_id}"
            })
        except Exception:
            pass
    return pd.DataFrame(asteroids_complete), len(hazardous_ids)

# --- TABS ---
tab_risk, tab_simulation, tab_orbit, tab_formulas, tab_apod = st.tabs([
    "🌎 Immediate Risk",
    "🛡️ Simulation & Mitigation",
    "🌌 3D Orbit Visualization",
    "📖 Formulas",
    "📸 NASA APOD"
])

# TAB: RISK
with tab_risk:
    if st.session_state.get('run_analysis'):
        df_results, total_found = get_hazardous_asteroid_details(st.session_state['start_date'], st.session_state['end_date'])
        if total_found > 0 and df_results is not None:
            st.success(f"Found **{total_found}** potentially hazardous asteroids!")
            st.dataframe(df_results, use_container_width=True)
        else:
            st.info("No hazardous asteroid found in this period.")

# TAB: SIMULATION
with tab_simulation:
    st.subheader("💡 Simulate an Asteroid Deflection")
    sim_diam = st.slider("Diameter (km)", 0.05, 5.0, 0.5)
    sim_vel = st.slider("Velocity (km/s)", 5.0, 50.0, 15.0)
    mit_delta_v = st.slider("Deflection (Delta-V m/s)", 0.0, 10.0, 1.0)

    sim_energy_base = calculate_impact_energy(sim_diam, sim_vel)
    sim_crater_base, _ = estimate_crater_size(sim_energy_base)
    conceptual_deflection_km = mit_delta_v * 5000000

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Estimated Energy", f"{sim_energy_base:.2f} Mt TNT")
        st.metric("Crater Diameter", f"{sim_crater_base:.2f} km")
    with col2:
        st.metric("Applied Deflection", f"{mit_delta_v} m/s")
        st.metric("Estimated Deflection", f"{conceptual_deflection_km:,.0f} km")

# TAB: ORBIT
with tab_orbit:
    st.subheader("🌌 Explore the Orbit in 3D")
    st.markdown("This 3D view shows a simple orbit path around the Sun — just like real asteroids do!")
    theta = np.linspace(0, 2*np.pi, 200)
    x = np.cos(theta)
    y = np.sin(theta)
    z = 0.2*np.sin(2*theta)

    fig = go.Figure(data=[go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(width=6, color='orange')),
                          go.Scatter3d(x=[0], y=[0], z=[0], mode='markers', marker=dict(size=12, color='yellow'), name='Sun')])
    fig.update_layout(scene=dict(xaxis_title='X (AU)', yaxis_title='Y (AU)', zaxis_title='Z (AU)'),
                      margin=dict(l=0, r=0, b=0, t=0))
    st.plotly_chart(fig, use_container_width=True)

# TAB: FORMULAS
with tab_formulas:
    st.subheader("📖 Formulas Used")
    st.markdown(r"""
    **Impact Energy:**
    \( E = 0.5 \times m \times v^2 \)  
    where  
    \( m = \frac{\pi}{6} \times D^3 \times \rho \)  

    **Crater Diameter:**
    \( D_c = 0.016 \times E^{1/3} \)  

    **Mass:**
    \( m = \frac{\pi}{6} \times D^3 \times \rho \)  

    **Kinetic Energy:**
    \( E = 0.5 \times m \times v^2 \)  

    **Deflection Distance:**
    \( \Delta x = \Delta v \times 5,000,000 \) (approximate)
    """, unsafe_allow_html=True)

# TAB: APOD
with tab_apod:
    st.subheader("📸 Explore NASA's Astronomy Picture of the Day (APOD)")
    st.markdown("""
    Choose any date to view NASA's Astronomy Picture of the Day (APOD) and learn more about it! 📸✨<br><br>
    🗓 Please note:<br>
    - You can select **any date from June 16, 1995** onwards.<br>
    - Future dates are not available.<br>
    - Each date shows a unique image or video from NASA's vast archive, accompanied by scientific explanations.<br><br>
    Explore the wonders of our universe and discover something new every day! 🌌
    """, unsafe_allow_html=True)

    apod_date = st.date_input("Choose a Date", date.today(),
                               min_value=date(1995, 6, 16),
                               max_value=date.today())

    if apod_date:
        date_str = apod_date.strftime("%Y-%m-%d")
        url, title, explanation = get_apod_data(API_KEY, query_date=date_str)

        if url:
            st.markdown(f"### {title}")
            if "youtube" in url or "vimeo" in url:
                st.video(url)
            else:
                st.image(url, use_container_width=True)

            with st.expander("Click for Scientific Explanation"):
                st.markdown(explanation)
        else:
            st.warning(f"Could not retrieve APOD image for date {date_str} or unsupported content.")

# --- FOOTER ---
st.markdown(f"""
<div class="footer">
This app uses official NASA APIs:<br>
🔗 <a href="{FEED_URL}" target="_blank">Near-Earth Object Feed API</a><br>
🔗 <a href="{LOOKUP_BASE_URL}" target="_blank">NEO Lookup API</a><br>
🔗 <a href="{APOD_URL}" target="_blank">Astronomy Picture of the Day (APOD) API</a><br>
<br>
💬 Created with love by <b>{TEAM_NAME}</b> — <i>{PARTICIPANTS}</i> — Santos-SP 🌠
</div>
""", unsafe_allow_html=True)
