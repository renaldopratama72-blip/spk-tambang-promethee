import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu # Wajib update requirements.txt
import time

# ==========================================
# 1. SETUP HALAMAN & TEMA
# ==========================================
st.set_page_config(
    page_title="Mining Decision System", 
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (The "Wow" Factor) ---
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Background bersih */
    .stApp {
        background-color: #f8f9fa;
    }

    /* Styling Kartu Metrik */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eef0f2;
        transition: transform 0.2s;
        text-align: center;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #1e293b;
    }
    .metric-label {
        color: #64748b;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Kartu Juara Besar */
    .hero-winner {
        background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
        color: white;
        padding: 40px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        position: relative;
        overflow: hidden;
    }
    .hero-winner::before {
        content: "🏆";
        position: absolute;
        right: -20px;
        top: -20px;
        font-size: 150px;
        opacity: 0.1;
        transform: rotate(15deg);
    }
    .hero-title {
        font-size: 1.2rem;
        opacity: 0.8;
        font-weight: 600;
    }
    .hero-name {
        font-size: 3.5rem;
        font-weight: 800;
        margin: 10px 0;
        background: -webkit-linear-gradient(#eee, #fff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONFIG DATA
# ==========================================
KRITERIA_CONFIG = {
    'C1':  {'nama': 'Skala Prod',     'tipe': 'max', 'bobot': 0.0225, 'q': 5,  'p': 20},
    'C2':  {'nama': 'Kebutuhan',      'tipe': 'max', 'bobot': 0.1035, 'q': 5,  'p': 20},
    'C3':  {'nama': 'Profitabilitas', 'tipe': 'max', 'bobot': 0.1440, 'q': 5,  'p': 20}, 
    'C4':  {'nama': 'COGS (Biaya)',   'tipe': 'min', 'bobot': 0.1845, 'q': 5,  'p': 20}, 
    'C5':  {'nama': 'Coal Supply',    'tipe': 'min', 'bobot': 0.0385, 'q': 5,  'p': 20}, 
    'C6':  {'nama': 'Perizinan',      'tipe': 'max', 'bobot': 0.1155, 'q': 2,  'p': 10},
    'C7':  {'nama': 'Kondisi Geo',    'tipe': 'max', 'bobot': 0.1960, 'q': 5,  'p': 20},
    'C8':  {'nama': 'RTRW',           'tipe': 'max', 'bobot': 0.0090, 'q': 2,  'p': 10},
    'C9':  {'nama': 'Karakteristik',  'tipe': 'max', 'bobot': 0.0255, 'q': 2,  'p': 10},
    'C10': {'nama': 'Sosial Mas',     'tipe': 'max', 'bobot': 0.0420, 'q': 2,  'p': 10},
    'C11': {'nama': 'Permit Ling',    'tipe': 'max', 'bobot': 0.0750, 'q': 2,  'p': 10},
    'C12': {'nama': 'Sektor Bisnis',  'tipe': 'max', 'bobot': 0.0035, 'q': 2,  'p': 10},
    'C13': {'nama': 'Rencana P',      'tipe': 'max', 'bobot': 0.0165, 'q': 2,  'p': 10},
    'C14': {'nama': 'Relasi',         'tipe': 'max', 'bobot': 0.0300, 'q': 2,  'p': 10},
}

# ==========================================
# 3. CORE LOGIC
# ==========================================
def hitung_promethee(df):
    data = df.copy()
    alternatives = data.index
    criteria = list(KRITERIA_CONFIG.keys())
    n = len(alternatives)
    total_bobot = sum(k['bobot'] for k in KRITERIA_CONFIG.values())
    preference_matrix = np.zeros((n, n))
    
    for k in criteria:
        if k not in data.columns: continue
        params = KRITERIA_CONFIG[k]
        col_data = pd.to_numeric(data[k], errors='coerce').fillna(0).values
        w = params['bobot'] / total_bobot if total_bobot > 0 else 0
        q, p = params['q'], params['p']
        is_max = params['tipe'] == 'max'
        
        for i in range(n):
            for j in range(n):
                if i == j: continue
                val_i, val_j = col_data[i], col_data[j]
                d = (val_i - val_j) if is_max else (val_j - val_i)
                
                pref = 0
                if d <= q: pref = 0
                elif d > p: pref = 1
                else: pref = (d - q) / (p - q)
                preference_matrix[i, j] += pref * w

    phi_plus = preference_matrix.sum(axis=1) / (n - 1)
    phi_minus = preference_matrix.sum(axis=0) / (n - 1)
    phi_net = phi_plus - phi_minus
    
    hasil = pd.DataFrame({
        'Net Flow': phi_net,
        'Leaving (+)': phi_plus,
        'Entering (-)': phi_minus
    }, index=alternatives)
    return hasil.sort_values(by='Net Flow', ascending=False)

# ==========================================
# 4. SIDEBAR NAVIGATION (MODERN)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040504.png", width=70)
    st.markdown("### SPK Tambang")
    
    # Modern Menu
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Data Input", "Tentang"],
        icons=["speedometer2", "table", "info-circle"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#f0f2f6"},
            "icon": {"color": "#2563eb", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#e2e8f0"},
            "nav-link-selected": {"background-color": "#2563eb"},
        }
    )
    
    st.divider()
    
    # Upload Zone
    st.markdown("**📂 Sumber Data**")
    uploaded_file = st.file_uploader("Upload Excel", type=['xlsx'], label_visibility="collapsed")
    
    st.divider()
    st.caption("Developed by **Renaldo Pratama**\nMM Universitas Bakrie")

# ==========================================
# 5. HALAMAN UTAMA
# ==========================================

if uploaded_file is None:
    # Tampilan Awal (Landing Page)
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown(
            """
            <div style="text-align: center; padding: 40px; background: white; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                <h1 style="color:#2563eb;">Selamat Datang! 👋</h1>
                <p style="font-size: 1.1rem; color: #666;">
                    Sistem Pendukung Keputusan Pemilihan IUP Terbaik.<br>
                    Silakan upload file Excel di menu sebelah kiri untuk memulai analisis.
                </p>
                <br>
                <img src="https://media.giphy.com/media/JQXaNxTb94V3x62g98/giphy.gif" width="100%" style="border-radius:10px;">
            </div>
            """, unsafe_allow_html=True
        )

elif selected == "Data Input":
    st.title("📂 Tinjauan Data Input")
    try:
        df = pd.read_excel(uploaded_file)
        df = df.set_index(df.columns[0])
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown("#### Tabel Data Mentah")
            st.dataframe(df.style.background_gradient(cmap="Blues"), use_container_width=True, height=500)
        with c2:
            st.markdown("#### Statistik")
            st.write(df.describe())
            
    except Exception as e:
        st.error("File tidak valid.")

elif selected == "Tentang":
    st.title("ℹ️ Tentang Aplikasi")
    st.markdown("""
    Aplikasi ini dibangun menggunakan metode **PROMETHEE II** (Preference Ranking Organization Method for Enrichment Evaluation).
    
    **Fitur Utama:**
    - Analisis Multi-Kriteria (14 Kriteria).
    - Perbandingan Pairwise otomatis.
    - Visualisasi Net Flow & Radar Chart.
    """)
    st.info("Dibuat khusus untuk Tesis MM Universitas Bakrie.")

elif selected == "Dashboard":
    # --- DASHBOARD ANALISIS ---
    try:
        df = pd.read_excel(uploaded_file)
        df = df.set_index(df.columns[0])
        
        # Validasi
        wajib = list(KRITERIA_CONFIG.keys())
        kurang = [c for c in wajib if c not in df.columns]
        
        if kurang:
            st.error(f"❌ Data Excel tidak valid. Kolom hilang: {kurang}")
        else:
            # Hitung
            hasil = hitung_promethee(df)
            best_mine = hasil.index[0]
            best_score = hasil.iloc[0]['Net Flow']
            
            # === HEADER JUARA (THE WOW MOMENT) ===
            st.markdown(f"""
            <div class="hero-winner">
                <div class="hero-title">REKOMENDASI KEPUTUSAN TERBAIK</div>
                <div class="hero-name">{best_mine}</div>
                <div style="font-size: 1.2rem; margin-top: 10px;">
                    💎 Skor Net Flow: <b>{best_score:.4f}</b> | Status: <span style="background: #2ecc71; padding: 2px 10px; border-radius: 5px; font-size: 0.9rem;">Sangat Direkomendasikan</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # === KPI CARDS ===
            col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
            with col_kpi1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{len(df)}</div>
                    <div class="metric-label">Jumlah Alternatif</div>
                </div>
                """, unsafe_allow_html=True)
            with col_kpi2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:#2563eb;">{hasil.iloc[1]['Net Flow']:.3f}</div>
                    <div class="metric-label">Runner Up ({hasil.index[1]})</div>
                </div>
                """, unsafe_allow_html=True)
            with col_kpi3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:#e11d48;">{hasil.iloc[-1]['Net Flow']:.3f}</div>
                    <div class="metric-label">Terendah ({hasil.index[-1]})</div>
                </div>
                """, unsafe_allow_html=True)
            with col_kpi4:
                gap = best_score - hasil.iloc[1]['Net Flow']
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:#10b981;">+{gap:.3f}</div>
                    <div class="metric-label">Gap Kemenangan</div>
                </div>
                """, unsafe_allow_html=True)

            st.write("<br>", unsafe_allow_html=True)

            # === CHARTS SECTION ===
            col_chart1, col_chart2 = st.columns([1.5, 1])
            
            with col_chart1:
                st.subheader("📊 Peringkat Performa (Net Flow)")
                # Bar Chart
                df_chart = hasil.reset_index()
                df_chart.columns = ['Alternatif', 'Net Flow', 'Leaving', 'Entering']
                df_chart['Warna'] = ['#0f172a' if x == best_mine else '#94a3b8' for x in df_chart['Alternatif']]
                
                fig_bar = px.bar(
                    df_chart, y='Alternatif', x='Net Flow', 
                    orientation='h', text_auto='.3f',
                    color='Alternatif', color_discrete_sequence=df_chart['Warna'].tolist()
                )
                fig_bar.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with col_chart2:
                st.subheader("🕸️ Profil Juara (Radar Chart)")
                # Radar Chart Logic (Normalisasi Data Juara vs Rata-rata)
                # Ambil data raw Juara
                winner_data = df.loc[best_mine].values
                # Normalisasi min-max sederhana untuk visualisasi (agar skalanya 0-1)
                df_norm = (df - df.min()) / (df.max() - df.min())
                winner_vals = df_norm.loc[best_mine].tolist()
                categories = df.columns.tolist()
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=winner_vals,
                    theta=categories,
                    fill='toself',
                    name=best_mine,
                    line_color='#2563eb'
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    showlegend=False,
                    height=400,
                    margin=dict(l=40, r=40, t=20, b=20)
                )
                st.plotly_chart(fig_radar, use_container_width=True)
                st.caption(f"Grafik di atas menunjukkan kekuatan {best_mine} (Biru) di setiap kriteria dibanding opsi lain.")

            # === TABEL DETAIL ===
            st.divider()
            with st.expander("📋 Lihat Tabel Analisis Lengkap"):
                st.dataframe(hasil.style.background_gradient(cmap="Blues"), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
