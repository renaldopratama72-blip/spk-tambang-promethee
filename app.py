import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time  # <--- Wajib ditambah untuk efek animasi loading

# --- 1. SETUP HALAMAN ---
st.set_page_config(page_title="SPK Tambang - Renaldo Pratama", layout="wide")

# ==========================================
# 2. DATABASE KRITERIA (UPDATED 4 DESIMAL)
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
# 3. FUNGSI HITUNG PROMETHEE
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
                d = col_data[i] - col_data[j] if is_max else col_data[j] - col_data[i]
                
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
# 4. TAMPILAN USER INTERFACE
# ==========================================

# --- HEADER & IDENTITAS ---
col_judul1, col_judul2 = st.columns([1, 15])
with col_judul1:
    st.write("# 🚜") 
with col_judul2:
    st.title("Sistem Pendukung Keputusan Tambang")

# Identitas Mahasiswa
st.markdown("""
<style>
.identity-box {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
    border-left: 5px solid #ff4b4b;
}
</style>
<div class="identity-box">
    <b>Oleh: Renaldo Pratama (2241011012)</b><br>
    Magister Managemen, Universitas Bakrie Jakarta
</div>
""", unsafe_allow_html=True)

st.markdown("### Metode: PROMETHEE II")

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. Upload Data")
    uploaded_file = st.file_uploader("Format Excel (.xlsx)", type=['xlsx'])
    
    st.divider()
    
    st.caption("Developed by:")
    st.caption("**Renaldo Pratama**")
    st.caption("2241011012 - Univ Bakrie")
    
    st.divider()
    
    with st.expander("Lihat Detail Bobot"):
        dt_info = [{"Kode": k, "Nama": v['nama'], "Bobot": f"{v['bobot']:.4f}"} for k, v in KRITERIA_CONFIG.items()]
        st.dataframe(pd.DataFrame(dt_info), hide_index=True)

# --- AREA UTAMA ---
if uploaded_file is None:
    st.info("👈 Silakan upload file Excel pada panel kiri untuk memulai analisis.")
else:
    try:
        df = pd.read_excel(uploaded_file)
        df = df.set_index(df.columns[0])
        
        wajib = list(KRITERIA_CONFIG.keys())
        kurang = [c for c in wajib if c not in df.columns]
        
        if kurang:
            st.error(f"❌ Kolom tidak lengkap! Hilang: {kurang}")
        else:
            # TAMPILKAN DATA AWAL
            st.subheader("📄 Data Awal")
            st.dataframe(df.head(), use_container_width=True)
            st.divider()

            # TOMBOL RUN
            col_btn1, col_btn2 = st.columns([1, 4])
            with col_btn1:
                tombol_hitung = st.button("🚀 JALANKAN ANALISIS", type="primary")
            
            if tombol_hitung:
                # -----------------------------------------------------------
                # BAGIAN ANIMASI LOADING TRUK
                # -----------------------------------------------------------
                
                # 1. Siapkan tempat kosong (placeholder) untuk animasi
                loading_placeholder = st.empty()
                
                # 2. Tampilkan GIF Truk di dalam placeholder
                with loading_placeholder.container():
                    # Anda bisa mengganti link GIF di bawah dengan link lain jika mau
                    gif_url = "https://i.gifer.com/origin/32/325263647366.gif" # Contoh GIF Truk/Excavator
                    st.markdown(f"""
                        <div style="text-align: center;">
                            <img src="{gif_url}" alt="Loading..." width="250">
                            <h3>🚧 Sedang Mengolah Data Tambang...</h3>
                        </div>
                    """, unsafe_allow_html=True)
                
                # 3. Simulasi delay agar animasi terlihat (opsional, 2 detik)
                time.sleep(2)
                
                # 4. Jalankan perhitungan
                hasil = hitung_promethee(df)
                best_mine = hasil.index[0]
                best_score = hasil.iloc[0]['Net Flow']

                # 5. Hapus animasi (kosongkan placeholder) setelah selesai
                loading_placeholder.empty()

                # -----------------------------------------------------------
                # BAGIAN HASIL (TIDAK ADA BALON LAGI)
                # -----------------------------------------------------------
                
                st.success("✅ Perhitungan Selesai!")
                # st.balloons() <-- Sudah dihapus sesuai request
                
                # Kotak Juara (4 Desimal)
                st.markdown(f"""
                <div style="background-color: #d4edda; padding: 20px; border-radius: 10px; border: 1px solid #c3e6cb; margin-bottom: 20px;">
                    <h2 style="color: #155724; margin:0;">🏆 Rekomendasi Terbaik: {best_mine}</h2>
                    <p style="color: #155724; margin:0;">Skor Net Flow: <strong>{best_score:.4f}</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Tabel (4 Desimal)
                st.subheader("📊 Tabel Peringkat Lengkap")
                try:
                    st.dataframe(
                        hasil.style.format("{:.4f}").background_gradient(cmap="RdYlGn", subset=['Net Flow']),
                        use_container_width=True
                    )
                except:
                    st.dataframe(hasil, use_container_width=True)

                st.divider()

                # Grafik
                st.subheader("📈 Grafik Visualisasi Net Flow")
                chart_data = hasil.sort_values(by='Net Flow', ascending=True)
                
                fig, ax = plt.subplots(figsize=(10, 6))
                warna = ['#28a745' if x >= 0 else '#dc3545' for x in chart_data['Net Flow']]
                bars = ax.barh(chart_data.index, chart_data['Net Flow'], color=warna)
                
                ax.axvline(0, color='black', linewidth=0.8)
                ax.set_title("Perbandingan Skor Net Flow (Promethee II)")
                ax.set_xlabel("Skor Net Flow")
                ax.grid(axis='x', linestyle='--', alpha=0.5)
                
                st.pyplot(fig)
                st.info("💡 **Cara Baca:** Kanan (Hijau) = Kinerja Positif. Kiri (Merah) = Kinerja Negatif.")

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")