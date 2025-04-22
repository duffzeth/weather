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

API_KEY = "Gqtw5BUEcQDIk4eb"
BASE_URL = "https://my.meteoblue.com/packages/basic-1h_clouds-1h"

# Streamlit UI
st.set_page_config(page_title="Meteo Aeropuertos Canarias", layout="centered")
st.title("🌦️ Consulta meteorológica - Aeropuertos de Canarias")

aeropuerto = st.selectbox("✈️ Selecciona un aeropuerto", list(aeropuertos.keys()))
fecha = st.date_input(
    "📅 Selecciona una fecha (máximo 3 días vista)",
    min_value=datetime.date.today(),
    max_value=datetime.date.today() + datetime.timedelta(days=3)
)
consultar = st.button("🔍 Consultar")

# Función pictograma
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

# Función visibilidad
def visibilidad_color(km):
    if km >= 10:
        return f"🟢 {km} km"
    elif km >= 5:
        return f"🟡 {km} km"
    else:
        return f"🔴 {km} km"

# === Ejecutar consulta ===
if consultar:
    lat, lon = aeropuertos[aeropuerto]
    url = (
        f"{BASE_URL}?lat={lat}&lon={lon}"
        f"&apikey={API_KEY}&format=json"
        f"&windspeed=kn&winddirection=degree"
    )

    response = requests.get(url)
    if response.status_code == 200:
        response_json = response.json()

        if "data_1h" in response_json:
            data = response_json["data_1h"]
            df = pd.DataFrame({
                "FechaHora": pd.to_datetime(data["time"]),
                "🌡️ Temp (°C)": data["temperature"],
                "🌬️ Viento (kt)": data["windspeed"],
                "🧭 Dirección (°)": data.get("winddirection", ["—"] * len(data["time"])),
                "☁️ Nubosidad (%)": data.get("cloudcover", ["—"] * len(data["time"])),
                "☁️ Techo nubes (m)": data.get("cloudbase", ["—"] * len(data["time"])),
                "👁️ Visibilidad (m)": data.get("visibility", ["—"] * len(data["time"])),
                "Icono": [pictocode_to_emoji(c) for c in data.get("pictocode", [0]*len(data["time"]))]
            })

            # Filtrar por fecha y franjas horarias deseadas
            fecha_str = fecha.strftime("%Y-%m-%d")
            horas_deseadas = ["06:00", "10:00", "14:00", "18:00", "22:00"]
            df["Hora"] = df["FechaHora"].dt.strftime("%H:%M")
            df["Fecha"] = df["FechaHora"].dt.strftime("%Y-%m-%d")
            df = df[df["Fecha"] == fecha_str]
            df = df[df["Hora"].isin(horas_deseadas)]

            if df.empty:
                st.warning("⚠️ No hay datos para esa fecha/franjas horarias.")
            else:
                # Formatear visibilidad
                df["👁️ Visibilidad (m)"] = df["👁️ Visibilidad (m)"].apply(
                    lambda m: visibilidad_color(round(m / 1000, 1)) if isinstance(m, (int, float)) else "—"
                )

                # Alerta por temperatura
                def alerta(temp):
                    if temp >= 30:
                        return "🔴"
                    elif temp >= 25:
                        return "🟡"
                    else:
                        return "🟢"

                df["🚨 Alerta"] = df["🌡️ Temp (°C)"].apply(alerta)
                df["📡 Origen"] = "Meteoblue"

                # Reordenar columnas
                columnas = ["Hora", "🌡️ Temp (°C)", "🌬️ Viento (kt)", "🧭 Dirección (°)", "☁️ Nubosidad (%)",
                            "☁️ Techo nubes (m)", "👁️ Visibilidad (m)", "Icono", "🚨 Alerta", "📡 Origen"]
                st.markdown(
                    df[columnas].to_html(index=False, justify="center", escape=False),
                    unsafe_allow_html=True
                )
        else:
            st.error("❌ No se encontraron datos horarios ('data_1h').")
    else:
        st.error(f"❌ Error al contactar con la API: {response.status_code}")
