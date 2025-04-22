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

def alerta(temp):
    if temp >= 30:
        return "🔴"
    elif temp >= 25:
        return "🟡"
    else:
        return "🟢"

st.set_page_config(page_title="Meteo Aeropuertos Canarias", layout="centered")
st.title("🌦️ Consulta meteorológica - Aeropuertos de Canarias")

aeropuerto = st.selectbox("✈️ Aeropuerto", list(aeropuertos.keys()))
fecha = st.date_input("📅 Fecha (hasta 3 días vista)", min_value=datetime.date.today(),
                      max_value=datetime.date.today() + datetime.timedelta(days=3))
consultar = st.button("🔍 Consultar")

if consultar:
    lat, lon = aeropuertos[aeropuerto]
    url = f"{BASE_URL}?lat={lat}&lon={lon}&apikey={API_KEY}&format=json&windspeed=kn&winddirection=degree"

    response = requests.get(url)
    if response.status_code == 200:
        json_data = response.json()
        if "data_1h" in json_data:
            data = json_data["data_1h"]
            df = pd.DataFrame({
                "FechaHora": pd.to_datetime(data["time"]),
                "Temp (°C)": data["temperature"],
                "Viento (kt)": data["windspeed"],
                "Dirección (°)": data.get("winddirection", [None]*len(data["time"])),
                "Icono": [pictocode_to_emoji(c) for c in data.get("pictocode", [0]*len(data["time"]))]
            })

            fecha_str = fecha.strftime("%Y-%m-%d")
            franjas = ["06:00", "10:00", "14:00", "18:00", "22:00"]
            df["Hora"] = df["FechaHora"].dt.strftime("%H:%M")
            df["Fecha"] = df["FechaHora"].dt.strftime("%Y-%m-%d")
            df = df[(df["Fecha"] == fecha_str) & (df["Hora"].isin(franjas))]

            if df.empty:
                st.warning("⚠️ No hay datos para esa fecha y franjas horarias.")
            else:
                df["Alerta"] = df["Temp (°C)"].apply(alerta)
                df["Origen"] = "Meteoblue"
                df = df[["Hora", "Temp (°C)", "Viento (kt)", "Dirección (°)", "Icono", "Alerta", "Origen"]]
                st.dataframe(df, use_container_width=True)
        else:
            st.error("❌ La respuesta no contiene 'data_1h'.")
    else:
        st.error(f"❌ Error al contactar con la API: {response.status_code}")
