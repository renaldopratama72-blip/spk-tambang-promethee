import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time

# ==========================================
# 1. SETUP & CONFIG HALAMAN
# ==========================================
st.set_page_config(
    page_title="SPK Tambang - Renaldo Pratama", 
    page_icon="⛏️",
    layout="wide"
)

# --- CUSTOM CSS UNTUK UI/UX ---
st.markdown("""
<style>
    /* Mengubah font header agar lebih elegan */
    h1, h2, h3 {
        font-family: 'Segoe UI', sans-serif;
        color: #2c3e50;
    }
    
    /* Styling Container Identitas */
    .identity-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #FF4B4B;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    
    /* Styling Kartu Juara */
    .winner-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 25px;
    }
    .winner-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 10px;
        opacity: 0.9;
    }
    .winner-name {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
    }
    .winner-score {
        font-size: 1.1rem;
        margin-top: 10px;
        background-color: rgba(255,255,255,0.2);
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
    }

    /* Mempercantik Tombol */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 50px;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
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
# 3. FUNGSI HITUNG (CORE LOGIC)
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
                val_i = col_data[i]
                val_j = col_data[j]
                
                # Hitung selisih
                d = (val_i - val_j) if is_max else (val_j - val_i)
                
                # Fungsi Preferensi
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
# 4. TAMPILAN USER INTERFACE (MODERN)
# ==========================================

# --- HEADER SECTION ---
col_head1, col_head2 = st.columns([1, 10])
with col_head1:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040504.png", width=80)
with col_head2:
    st.title("Sistem Pendukung Keputusan Tambang")
    st.caption("Analisis Pemilihan IUP Terbaik Menggunakan Metode **PROMETHEE II**")

st.markdown("""
<div class="identity-box">
    <h4 style="margin:0; color:#333;">👤 Oleh: Renaldo Pratama (2241011012)</h4>
    <p style="margin:0; color:#666;">Magister Managemen, Universitas Bakrie Jakarta</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROL ---
with st.sidebar:
    st.header("📂 Panel Kontrol")
    uploaded_file = st.file_uploader("Upload File Excel (.xlsx)", type=['xlsx'])
    
    st.divider()
    
    with st.expander("ℹ️ Referensi Bobot Kriteria"):
        dt_info = [{"Kode": k, "Nama": v['nama'], "Tipe": v['tipe'].upper(), "Bobot": f"{v['bobot']:.4f}"} for k, v in KRITERIA_CONFIG.items()]
        st.dataframe(pd.DataFrame(dt_info), hide_index=True)
    
    st.info("Pastikan format Excel kolom pertama adalah Nama IUP, diikuti kolom C1 sd C14.")

# --- MAIN CONTENT AREA ---
if uploaded_file is None:
    # Tampilan kosong yang ramah (Empty State)
    st.warning("👈 **Belum ada data.** Silakan upload file Excel pada panel di sebelah kiri untuk memulai.")
    
    # Contoh ilustrasi (optional)
    col_mock1, col_mock2 = st.columns(2)
    with col_mock1:
        st.markdown("#### Cara Penggunaan:")
        st.markdown("""
        1. Siapkan file Excel.
        2. Upload di sidebar kiri.
        3. Klik tombol **Jalankan Analisis**.
        4. Tunggu animasi selesai.
        """)

else:
    try:
        # Load Data
        df = pd.read_excel(uploaded_file)
        df = df.set_index(df.columns[0])
        
        # Cek Validitas
        wajib = list(KRITERIA_CONFIG.keys())
        kurang = [c for c in wajib if c not in df.columns]
        
        if kurang:
            st.error(f"❌ Kolom Excel tidak lengkap! Kolom hilang: {kurang}")
        else:
            # --- TABS NAVIGATION (Agar rapi) ---
            tab1, tab2 = st.tabs(["📄 Data Input", "🚀 Hasil Analisis"])
            
            # --- TAB 1: DATA ---
            with tab1:
                st.subheader("Preview Data Mentah")
                st.dataframe(df, use_container_width=True)
            
            # --- TAB 2: PROSES & HASIL ---
            with tab2:
                col_btn_center, _ = st.columns([1, 2])
                with col_btn_center:
                    tombol_hitung = st.button("🚀 JALANKAN ANALISIS", type="primary")
                
                if tombol_hitung:
                    # === AREA ANIMASI LOADING ===
                    placeholder_animasi = st.empty()
                    with placeholder_animasi.container():
                        gif_url = "https://i.gifer.com/origin/32/325263647366.gif"
                        st.markdown(f"""
                            <div style="text-align: center; margin: 40px 0;">
                                <img src="{gif_url}" style="border-radius: 10px; max-width: 300px;">
                                <h3 style="color: #555;">🚧 Sedang Mengangkut Data...</h3>
                                <p>Mohon tunggu sebentar, mesin sedang bekerja.</p>
                            </div>
                        """, unsafe_allow_html=True)
                        time.sleep(2.5) # Durasi animasi
                    
                    placeholder_animasi.empty() # Hapus animasi
                    
                    # === HITUNG ===
                    hasil = hitung_promethee(df)
                    best_mine = hasil.index[0]
                    best_score = hasil.iloc[0]['Net Flow']
                    worst_mine = hasil.index[-1]
                    worst_score = hasil.iloc[-1]['Net Flow']

                    # === TAMPILAN HASIL UTAMA (WINNER CARD) ===
                    st.markdown(f"""
                    <div class="winner-card">
                        <div class="winner-title">🏆 REKOMENDASI TERBAIK</div>
                        <div class="winner-name">{best_mine}</div>
                        <div class="winner-score">Net Flow: {best_score:.4f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # === METRICS ROW ===
                    col_m1, col_m2, col_m3 = st.columns(3)
                    col_m1.metric("Jumlah Alternatif", f"{len(df)} Tambang")
                    col_m2.metric("Skor Tertinggi", f"{best_score:.4f}")
                    col_m3.metric("Skor Terendah", f"{worst_score:.4f}", delta_color="inverse")
                    
                    st.divider()

                    # === LAYOUT GRAFIK & TABEL ===
                    col_res1, col_res2 = st.columns([2, 1])
                    
                    with col_res1:
                        st.subheader("📈 Grafik Visualisasi")
                        # Setup Data
                        chart_data = hasil.sort_values(by='Net Flow', ascending=True)
                        colors = ['#ff4b4b' if x < 0 else '#00cc96' for x in chart_data['Net Flow']]
                        
                        # Plotting Matplotlib Modern
                        fig, ax = plt.subplots(figsize=(8, 5))
                        ax.barh(chart_data.index, chart_data['Net Flow'], color=colors, height=0.6)
                        
                        # Styling Chart (Hilangkan border kaku)
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        ax.spines['left'].set_visible(False)
                        ax.spines['bottom'].set_color('#DDD')
                        
                        ax.axvline(0, color='grey', linewidth=0.8, linestyle='--')
                        ax.set_xlabel("Skor Net Flow", fontsize=9, color='grey')
                        ax.tick_params(axis='x', colors='grey')
                        
                        st.pyplot(fig)
                        
                    with col_res2:
                        st.subheader("📊 Peringkat Detail")
                        st.dataframe(
                            hasil[['Net Flow']].style.format("{:.4f}").background_gradient(cmap="RdYlGn"),
                            use_container_width=True,
                            height=400
                        )
                    
                    # === DOWNLOAD BUTTON ===
                    st.divider()
                    csv = hasil.to_csv().encode('utf-8')
                    st.download_button(
                        label="📥 Download Laporan Lengkap (CSV)",
                        data=csv,
                        file_name='hasil_analisis_promethee.csv',
                        mime='text/csv',
                    )

    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")
