import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import date, timedelta

# --- 1. SETUP HALAMAN WEB ---
st.set_page_config(page_title="Dashboard Kurs Realtime", layout="wide")
st.title("Dashboard Realtime: Kurs USD ke IDR")
st.write("Aplikasi ini mengambil data realtime dari API frankfurter publik dan menampilkannya data serta visualisasinya.")
st.markdown("---")

# --- 2. FUNGSI AMBIL DATA (Dicache agar cepat) ---
@st.cache_data(ttl=3600)
def load_data():
    today = date.today()
    start_date = today - timedelta(days=30)
    url = f"https://api.frankfurter.app/{start_date}..?from=USD&to=IDR"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        rates_data = []
        for tgl, rate in data['rates'].items():
            rates_data.append({
                "tanggal": tgl,
                "kurs_idr": rate['IDR']
            })
        df = pd.DataFrame(rates_data)
        df['tanggal'] = pd.to_datetime(df['tanggal'])
        return df
    except Exception as e:
        st.error(f"Gagal mengambil data: {e}")
        return pd.DataFrame()

# --- 3. LOAD DATA ---
with st.spinner('Sedang menarik data terbaru dari API...'):
    df = load_data()

if not df.empty:
    col1, col2 = st.columns([1, 2])

    # --- BAGIAN KIRI: DATAFRAME ---
    with col1:
        st.subheader("📋 Data Tabel (30 Hari)")
        st.dataframe(df.sort_values('tanggal', ascending=False), height=400, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data CSV",
            data=csv,
            file_name=f"kurs_usd_idr_{date.today()}.csv",
            mime="text/csv",
        )

    # --- BAGIAN KANAN: VISUALISASI LEBIH JELAS (ALTAIR) ---
    with col2:
        st.subheader("📈 Grafik Pergerakan Kurs USD - IDR")
        
        # Membuat grafik interaktif dengan Altair
        chart = alt.Chart(df).mark_line(point=True, color='red').encode(
            x=alt.X('tanggal', title='Tanggal', axis=alt.Axis(format='%d %b')),
            y=alt.Y('kurs_idr', title='Kurs (IDR)', scale=alt.Scale(zero=False)), # zero=False agar fluktuasi terlihat jelas
            tooltip=[
                alt.Tooltip('tanggal', title='Tanggal', format='%d %B %Y'),
                alt.Tooltip('kurs_idr', title='Kurs IDR', format=',.0f')
            ]
        ).properties(
            height=400 # Tinggi grafik agar proporsional
        ).interactive() # Membuat grafik bisa di-zoom dan digeser

        st.altair_chart(chart, use_container_width=True)

        # Statistik Ringkas
        st.markdown("#### Statistik Ringkas")
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Harga Terakhir", f"Rp {df['kurs_idr'].iloc[-1]:,.0f}")
        kpi2.metric("Tertinggi (30d)", f"Rp {df['kurs_idr'].max():,.0f}")
        kpi3.metric("Terendah (30d)", f"Rp {df['kurs_idr'].min():,.0f}")

else:
    st.warning("Data tidak ditemukan. Coba refresh halaman beberapa saat lagi.")