import streamlit as st
import requests
import datetime
import pandas as pd

# Aeropuertos y coordenadas
aeropuertos = {
    "GCLP - Gran Canaria": (27.9319, -15.3866),
    "GCXO - Tenerife Norte": (28.4827, -16.3415),
    "GCFV - Fuerteventura": (28.4527, -13.8638),
    "GCRR - Lanzarote": (28.9455, -13.6052),
    "GCLA - La Palma": (28.6265, -17.7556),
    "GCHI - El Hierro": (27.8148, -17.8871),
    "GCGM - La Gomera": (28.0296, -17.2146),
}

API_KEY = "gVphN31ARLcKGzX7"
BASE_URL = "https://my.meteoblue.com/packages/basic-1h_basic-day_clouds-1h_clouds-day"

def pictocode_to_emoji(code):
    if code == 1:
        return "☀️"
    elif code == 2:
        return "🌤️"
    elif code in [3, 4]:
        return "☁️"
    elif code in [5, 6]:
        return "🌧️"
    else:
        return "⛈️"

def visibilidad_color(km):
    if km >= 10:
        return f"🟢 {km} km"
    elif km >= 5:
        return f"🟡 {km} km"
    else:
        return f"🔴 {km} km"

def alerta(temp):
    if temp >= 30:
        return "🔴"
    elif temp >= 25:
        return "🟡"
    else:
        return "🟢"

# === Interfaz ===
st.set_page_config(page_title="Meteo Aeropuertos Canarias", layout="centered")

st.markdown("<h1 style='text-align: center;'>🌦️ Consulta meteorológica - Aeropuertos de Canarias</h1>", unsafe_allow_html=True)

aeropuerto = st.selectbox("✈️ Aeropuerto", list(aeropuertos.keys()))
fecha = st.date_input(
    "📅 Fecha (hasta 3 días vista)",
    min_value=datetime.date.today(),
    max_value=datetime.date.today() + datetime.timedelta(days=3)
)
consultar = st.button("🔍 Consultar")

# === Lógica principal ===
if consultar:
    lat, lon = aeropuertos[aeropuerto]
    url = (
        f"{BASE_URL}?lat={lat}&lon={lon}"
        f"&apikey={API_KEY}&format=json"
        f"&windspeed=kn&winddirection=degree"
    )

    response = requests.get(url)
    if response.status_code == 200:
        json_data = response.json()

        if "data_1h" in json_data:
            data = json_data["data_1h"]
            df = pd.DataFrame({
                "FechaHora": pd.to_datetime(data["time"]),
                "🌡️ Temp (°C)": data["temperature"],
                "🌬️ Viento (kt)": data["windspeed"],
                "🧭 Dirección (°)": data.get("winddirection", [None]*len(data["time"])),
                "☁️ Nubosidad (%)": data.get("cloudcover", [None]*len(data["time"])),
                "☁️ Techo nubes (m)": data.get("cloudbase", [None]*len(data["time"])),
                "👁️ Visibilidad (m)": data.get("visibility", [None]*len(data["time"])),
                "Icono": [pictocode_to_emoji(c) for c in data.get("pictocode", [0]*len(data["time"]))]
            })

            # Filtrar por fecha y franjas horarias
            fecha_str = fecha.strftime("%Y-%m-%d")
            df["Hora"] = df["FechaHora"].dt.strftime("%H:%M")
            df["Fecha"] = df["FechaHora"].dt.strftime("%Y-%m-%d")
            franjas = ["06:00", "10:00", "14:00", "18:00", "22:00"]
            df = df[(df["Fecha"] == fecha_str) & (df["Hora"].isin(franjas))]

            if df.empty:
                st.warning("⚠️ No hay datos para esa fecha y franjas horarias.")
            else:
                df["👁️ Visibilidad (m)"] = df["👁️ Visibilidad (m)"].apply(
                    lambda m: visibilidad_color(round(m / 1000, 1)) if isinstance(m, (int, float)) else "—"
                )
                df["🚨 Alerta"] = df["🌡️ Temp (°C)"].apply(alerta)
                df["📡 Origen"] = "Meteoblue"

                columnas = ["Hora", "🌡️ Temp (°C)", "🌬️ Viento (kt)", "🧭 Dirección (°)",
                            "☁️ Nubosidad (%)", "☁️ Techo nubes (m)", "👁️ Visibilidad (m)",
                            "Icono", "🚨 Alerta", "📡 Origen"]

                # === Tabla visual con mejor compatibilidad ===
                html_table = f"""
                <style>
                    .custom-container {{
                        display: flex;
                        justify-content: center;
                    }}
                    .custom-table {{
                        border-collapse: collapse;
                        width: 95%;
                        max-width: 900px;
                        background-color: #fff;
                        color: #000;
                        font-family: Arial, sans-serif;
                        margin: 0 auto;
                        border-radius: 8px;
                        overflow: hidden;
                    }}
                    .custom-table th, .custom-table td {{
                        border: 1px solid #ccc;
                        padding: 10px;
                        text-align: center;
                    }}
                    .custom-table th {{
                        background-color: #e6e6e6;
                        color: #333;
                    }}
                    .custom-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .custom-table tr:hover {{ background-color: #f1f1f1; }}
                </style>

                <div class="custom-container">
                    <div>
                        <h3 style="text-align: center;">🌍 Resultados meteorológicos para {aeropuerto.split('-')[0].strip()} ({fecha_str})</h3>
                        <div style="overflow-x: auto;">
                            {df[columnas].to_html(classes='custom-table', index=False, escape=False)}
                        </div>
                    </div>
                </div>
                """

                st.markdown(html_table, unsafe_allow_html=True)
        else:
            st.error("❌ La respuesta no contiene 'data_1h'.")
    else:
        st.error(f"❌ Error al contactar con la API: {response.status_code}")
