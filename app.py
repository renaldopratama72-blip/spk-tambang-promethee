import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px  # Library grafik interaktif
import time

# ==========================================
# 1. SETUP & CONFIG HALAMAN
# ==========================================
st.set_page_config(
    page_title="Executive Dashboard - SPK Tambang", 
    page_icon="⛏️",
    layout="wide"
)

# --- CUSTOM CSS (PROFESSIONAL LOOK) ---
st.markdown("""
<style>
    /* Font & Headers */
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #1e293b; }
    
    /* Winner Card */
    .winner-container {
        background: linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%);
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid #ffffff;
    }
    .winner-label { font-size: 1.2rem; color: #155724; font-weight: 600; letter-spacing: 1px; }
    .winner-name { font-size: 3rem; color: #0f5132; font-weight: 800; margin: 10px 0; }
    .winner-score { font-size: 1.4rem; color: #155724; background: rgba(255,255,255,0.4); padding: 5px 20px; border-radius: 30px; display: inline-block;}

    /* Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Tombol */
    .stButton > button {
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        height: 50px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(37, 99, 235, 0.3); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE KRITERIA
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
# 4. USER INTERFACE
# ==========================================

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040504.png", width=60)
    st.header("Panel Kontrol")
    uploaded_file = st.file_uploader("Upload Data (.xlsx)", type=['xlsx'])
    
    st.divider()
    with st.expander("ℹ️ Parameter Kriteria"):
        dt_info = [{"Kode": k, "Nama": v['nama'], "Tipe": v['tipe'].upper(), "Bobot": f"{v['bobot']:.4f}"} for k, v in KRITERIA_CONFIG.items()]
        st.dataframe(pd.DataFrame(dt_info), hide_index=True)
    
    st.markdown("---")
    st.caption("**Renaldo Pratama** (2241011012)\nMM Universitas Bakrie")

# --- MAIN PAGE ---
col_logo, col_title = st.columns([1, 8])
with col_title:
    st.title("Sistem Keputusan Tambang")
    st.markdown("Dashboard Analisis Pemilihan IUP Terbaik (Metode PROMETHEE II)")

if uploaded_file is None:
    # Empty State
    st.info("👋 Selamat Datang! Silakan upload file Excel di sidebar sebelah kiri untuk memulai.")
else:
    try:
        df = pd.read_excel(uploaded_file)
        df = df.set_index(df.columns[0])
        
        # Validasi
        wajib = list(KRITERIA_CONFIG.keys())
        kurang = [c for c in wajib if c not in df.columns]
        
        if kurang:
            st.error(f"❌ Data Excel tidak valid. Kolom hilang: {kurang}")
        else:
            # --- TABS ---
            tab_data, tab_hasil = st.tabs(["📊 Data Input (Heatmap)", "🚀 Dashboard Keputusan"])
            
            with tab_data:
                st.markdown("### 🔍 Peta Data Input")
                st.markdown("Warna **Biru Gelap** menandakan nilai tinggi, **Putih** menandakan nilai rendah.")
                # Heatmap Data Input
                st.dataframe(
                    df.style.background_gradient(cmap="Blues"),
                    use_container_width=True,
                    height=400
                )
            
            with tab_hasil:
                col_btn, _ = st.columns([1, 2])
                if col_btn.button("JALANKAN ANALISIS", type="primary"):
                    
                    # Animasi Loading
                    with st.spinner("⏳ Sedang menghitung preferensi, threshold, dan net flow..."):
                        time.sleep(1.5)
                        hasil = hitung_promethee(df)
                        
                    best_mine = hasil.index[0]
                    best_score = hasil.iloc[0]['Net Flow']
                    
                    # --- 1. WINNER BANNER ---
                    st.markdown(f"""
                    <div class="winner-container">
                        <div class="winner-label">REKOMENDASI TERBAIK</div>
                        <div class="winner-name">{best_mine}</div>
                        <div class="winner-score">Net Flow: {best_score:.4f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # --- 2. METRICS ---
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Top Performer", best_mine, delta="Juara 1")
                    c2.metric("Runner Up", hasil.index[1], delta=f"{hasil.iloc[1]['Net Flow']:.4f}")
                    c3.metric("Lowest Performer", hasil.index[-1], delta=f"{hasil.iloc[-1]['Net Flow']:.4f}", delta_color="inverse")
                    
                    st.divider()
                    
                    # --- 3. INTERACTIVE CHART (PLOTLY) ---
                    col_chart, col_table = st.columns([2, 1])
                    
                    with col_chart:
                        st.subheader("📈 Visualisasi Net Flow")
                        
                        # Siapkan data untuk Plotly
                        df_chart = hasil.reset_index()
                        df_chart.columns = ['Alternatif', 'Net Flow', 'Leaving', 'Entering']
                        df_chart['Status'] = ['Positif' if x >= 0 else 'Negatif' for x in df_chart['Net Flow']]
                        
                        # Membuat Chart Interaktif
                        fig = px.bar(
                            df_chart, 
                            x="Net Flow", 
                            y="Alternatif", 
                            color="Status",
                            orientation='h',
                            color_discrete_map={'Positif': '#2ecc71', 'Negatif': '#e74c3c'},
                            text_auto='.4f',
                            hover_data=['Leaving', 'Entering']
                        )
                        
                        fig.update_layout(
                            xaxis_title="Skor Net Flow",
                            yaxis_title="Nama IUP",
                            showlegend=False,
                            height=400,
                            margin=dict(l=0, r=0, t=30, b=0)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        st.caption("*Arahkan kursor ke batang grafik untuk melihat detail nilai Leaving & Entering flow.*")

                    with col_table:
                        st.subheader("📋 Peringkat Detail")
                        st.dataframe(
                            hasil[['Net Flow']].style.background_gradient(cmap="RdYlGn"),
                            use_container_width=True,
                            height=400
                        )

                    # --- 4. DOWNLOAD ---
                    st.divider()
                    st.download_button(
                        label="📥 Download Laporan (CSV)",
                        data=hasil.to_csv().encode('utf-8'),
                        file_name='Laporan_SPK_Promethee.csv',
                        mime='text/csv'
                    )

    except Exception as e:
        st.error(f"Terjadi error pada file: {e}")
