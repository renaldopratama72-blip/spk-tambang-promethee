import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
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

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8f9fa; }

    /* Insight Box */
    .insight-box {
        background-color: #ffffff;
        border-left: 6px solid #2563eb;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-top: 30px;
        margin-bottom: 30px;
    }
    .insight-title { font-weight: 800; color: #1e293b; font-size: 1.2rem; margin-bottom: 15px; display: flex; align-items: center; }
    .insight-title::before { content: "📝"; margin-right: 10px; font-size: 1.4rem; }
    .insight-text { color: #475569; line-height: 1.7; font-size: 1.05rem; }
    .strength-tag { background: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.95em; border: 1px solid #bbf7d0; }
    .weakness-tag { background: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.95em; border: 1px solid #fecaca; }

    /* Kartu Metrik */
    .metric-card {
        background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eef0f2;
        text-align: center; transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    .metric-value { font-size: 2rem; font-weight: 800; color: #1e293b; }
    .metric-label { color: #64748b; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }

    /* Kartu Juara */
    .hero-winner {
        background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
        color: white; padding: 40px; border-radius: 20px; margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2); position: relative; overflow: hidden;
    }
    .hero-winner::before {
        content: "🏆"; position: absolute; right: -20px; top: -20px;
        font-size: 150px; opacity: 0.1; transform: rotate(15deg);
    }
    .hero-name {
        font-size: 3.5rem; font-weight: 800; margin: 10px 0;
        background: -webkit-linear-gradient(#eee, #fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
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
    
    hasil = pd.DataFrame({'Net Flow': phi_net, 'Leaving (+)': phi_plus, 'Entering (-)': phi_minus}, index=alternatives)
    return hasil.sort_values(by='Net Flow', ascending=False)

def generate_insight(df, winner_name):
    df_norm = df.copy()
    for col in df_norm.columns:
        if col in KRITERIA_CONFIG:
            is_max = KRITERIA_CONFIG[col]['tipe'] == 'max'
            if is_max:
                df_norm[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min()) if (df[col].max() - df[col].min()) != 0 else 0
            else:
                df_norm[col] = (df[col].max() - df[col]) / (df[col].max() - df[col].min()) if (df[col].max() - df[col].min()) != 0 else 0
    
    winner_scores = df_norm.loc[winner_name]
    top_3 = winner_scores.nlargest(3).index.tolist()
    top_3_names = [f"{KRITERIA_CONFIG[c]['nama']}" for c in top_3]
    weak_1 = winner_scores.nsmallest(1).index.tolist()
    weak_1_name = KRITERIA_CONFIG[weak_1[0]]['nama'] if weak_1 else "Tidak ada"
    return top_3_names, weak_1_name

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040504.png", width=70)
    st.markdown("### SPK Tambang")
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Data Input", "Panduan"],
        icons=["speedometer2", "table", "book"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#f0f2f6"},
            "icon": {"color": "#2563eb", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#e2e8f0"},
            "nav-link-selected": {"background-color": "#2563eb"},
        }
    )
    st.divider()
    st.markdown("**📂 Sumber Data**")
    uploaded_file = st.file_uploader("Upload Excel", type=['xlsx'], label_visibility="collapsed")
    st.divider()
    st.caption("Developed by **Renaldo Pratama**\nMM Universitas Bakrie")

# ==========================================
# 5. HALAMAN UTAMA
# ==========================================

if uploaded_file is None:
    # --- LANDING PAGE ---
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color:#2563eb; font-weight:800;">Selamat Datang! 👋</h1>
                <p style="font-size: 1.1rem; color: #666;">
                    <b>Sistem Pendukung Keputusan Pemilihan IUP Terbaik</b><br>
                    Metode PROMETHEE II untuk Analisis Strategis Tambang.
                </p>
            </div>
            """, unsafe_allow_html=True
        )
        st.image(
            "https://images.squarespace-cdn.com/content/v1/5acda2f4c258b4bd2d14dca2/1653447668933-C9BBM4LAGE1BBEINI7FP/Perusahaan+Tambang+di+Bursa+Efek+Indonesia.jpg?format=2500w",
            caption="Ilustrasi: Sektor Pertambangan di Indonesia",
            use_container_width=True
        )
        st.markdown(
            """
            <div style="text-align: center; margin-top: 25px; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <p style="color: #475569; font-size: 0.95rem; margin: 0;">
                    👈 Silakan <b>upload file data Excel (.xlsx)</b> pada menu di sebelah kiri untuk memulai analisis.
                </p>
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
        st.error("File tidak valid atau belum diupload.")

elif selected == "Panduan":
    st.title("ℹ️ Panduan & Spesifikasi Data")
    st.markdown("""
    Agar sistem dapat menghitung skor PROMETHEE II dengan akurat, mohon perhatikan spesifikasi data di bawah ini.
    """)
    
    # --- Bagian 1: Kamus Data (Penjelasan C1-C14) ---
    st.subheader("1. Kriteria Penilaian (Kamus Data)")
    st.markdown("Data Excel Anda **wajib** memiliki kolom dengan kode kriteria berikut:")
    
    # Membuat DataFrame untuk tampilan Kamus Data yang rapi
    dict_data = []
    for k, v in KRITERIA_CONFIG.items():
        arah = "Maksimal (Nilai Tinggi Lebih Baik)" if v['tipe'] == 'max' else "Minimal (Nilai Rendah Lebih Baik)"
        dict_data.append({"Kode": k, "Nama Kriteria": v['nama'], "Sifat Kriteria": arah})
    
    df_kamus = pd.DataFrame(dict_data)
    st.dataframe(
        df_kamus.style.applymap(lambda x: 'color: red; font-weight:bold' if 'Minimal' in x else 'color: green', subset=['Sifat Kriteria']), 
        use_container_width=True, 
        hide_index=True
    )
    
    # --- Bagian 2: Contoh Format Tabel ---
    st.divider()
    st.subheader("2. Format Tabel Excel (.xlsx)")
    st.info("⚠️ **PENTING:** Judul Kolom (Header) harus menggunakan KODE (**C1, C2, dst**), bukan nama kriteria.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Contoh Struktur Data yang Benar:**")
        # Contoh Dummy Data
        dummy_data = {
            "Nama Alternatif": ["IUP Tambang A", "IUP Tambang B", "IUP Tambang C"],
            "C1": [5000, 7500, 6000],
            "C2": [8, 9, 7],
            "C3": [15, 20, 18],
            "C...": ["...", "...", "..."],
            "C14": [90, 85, 88]
        }
        st.table(pd.DataFrame(dummy_data))
    
    with c2:
        st.markdown("**Keterangan:**")
        st.markdown("""
        * **Kolom 1:** Nama Alternatif / Perusahaan Tambang.
        * **Kolom C1 - C14:** Masukkan nilai numerik (angka).
        * Pastikan tidak ada sel yang kosong (blank).
        """)

elif selected == "Dashboard":
    try:
        df = pd.read_excel(uploaded_file)
        df = df.set_index(df.columns[0])
        
        wajib = list(KRITERIA_CONFIG.keys())
        kurang = [c for c in wajib if c not in df.columns]
        
        if kurang:
            st.error(f"❌ Data Excel tidak valid. Kolom berikut hilang: {kurang}. Silakan cek menu 'Panduan' untuk format yang benar.")
        else:
            # Hitung & Insight
            hasil = hitung_promethee(df)
            best_mine = hasil.index[0]
            best_score = hasil.iloc[0]['Net Flow']
            strengths, weakness = generate_insight(df, best_mine)
            
            # Bagian 1: Parameter
            st.subheader("1. Parameter & Konfigurasi Model")
            with st.expander("ℹ️ Lihat Detail Bobot & Threshold (Q/P) yang Digunakan", expanded=False):
                param_data = []
                for k, v in KRITERIA_CONFIG.items():
                    param_data.append({
                        "Kode": k,
                        "Nama Kriteria": v['nama'],
                        "Tipe": v['tipe'].upper(),
                        "Bobot": f"{v['bobot']:.4f}",
                        "Q (Indifference)": v['q'],
                        "P (Preference)": v['p']
                    })
                param_df = pd.DataFrame(param_data)
                st.dataframe(
                    param_df.style.applymap(lambda x: 'background-color: #e2e8f0' if x in ['MIN'] else '', subset=['Tipe']),
                    use_container_width=True, 
                    hide_index=True
                )
                st.caption("*Catatan: Tipe 'MIN' berarti semakin kecil nilai semakin baik (contoh: Biaya).")
            
            st.divider()
            st.subheader("2. Hasil Analisis Keputusan")

            # Hero Section
            st.markdown(f"""
            <div class="hero-winner">
                <div class="hero-title">REKOMENDASI KEPUTUSAN TERBAIK</div>
                <div class="hero-name">{best_mine}</div>
                <div style="font-size: 1.2rem; margin-top: 10px;">
                    💎 Skor Net Flow: <b>{best_score:.4f}</b> | Status: <span style="background: #2ecc71; padding: 2px 10px; border-radius: 5px; font-size: 0.9rem;">Sangat Direkomendasikan</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # KPI Cards
            col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
            with col_kpi1:
                st.markdown(f"<div class='metric-card'><div class='metric-value'>{len(df)}</div><div class='metric-label'>Jumlah Alternatif</div></div>", unsafe_allow_html=True)
            with col_kpi2:
                st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#2563eb;'>{hasil.iloc[1]['Net Flow']:.3f}</div><div class='metric-label'>Runner Up ({hasil.index[1]})</div></div>", unsafe_allow_html=True)
            with col_kpi3:
                st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#e11d48;'>{hasil.iloc[-1]['Net Flow']:.3f}</div><div class='metric-label'>Terendah ({hasil.index[-1]})</div></div>", unsafe_allow_html=True)
            with col_kpi4:
                gap = best_score - hasil.iloc[1]['Net Flow']
                st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#10b981;'>+{gap:.3f}</div><div class='metric-label'>Gap Kemenangan</div></div>", unsafe_allow_html=True)

            st.write("<br>", unsafe_allow_html=True)

            # Charts
            c1, c2 = st.columns([1.5, 1])
            with c1:
                st.subheader("📊 Peringkat Performa")
                df_chart = hasil.reset_index()
                df_chart.columns = ['Alternatif', 'Net Flow', 'Leaving', 'Entering']
                df_chart['Warna'] = ['#0f172a' if x == best_mine else '#94a3b8' for x in df_chart['Alternatif']]
                fig = px.bar(df_chart, y='Alternatif', x='Net Flow', orientation='h', text_auto='.3f', color='Alternatif', color_discrete_sequence=df_chart['Warna'].tolist())
                fig.update_layout(showlegend=False, height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                st.subheader("🕸️ Profil Juara")
                winner_vals = ((df - df.min()) / (df.max() - df.min())).loc[best_mine].tolist()
                fig_radar = go.Figure(go.Scatterpolar(r=winner_vals, theta=df.columns.tolist(), fill='toself', name=best_mine))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False, height=400, margin=dict(l=40, r=40, t=20, b=20))
                st.plotly_chart(fig_radar, use_container_width=True)

            # Bagian 3: Insight (Bottom)
            st.write("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">Catatan & Rekomendasi untuk Manajemen</div>
                <div class="insight-text">
                    Berdasarkan hasil analisis komputasi menggunakan metode PROMETHEE II dengan parameter di atas, <b>{best_mine}</b> terpilih sebagai opsi paling optimal.
                    <br><br>
                    <ul>
                        <li><b>Keunggulan Kompetitif:</b> IUP ini menunjukkan performa superior (dominan) terutama pada aspek fundamental: 
                        <span class="strength-tag">{strengths[0]}</span>, <span class="strength-tag">{strengths[1]}</span>, dan <span class="strength-tag">{strengths[2]}</span>.</li>
                        <br>
                        <li><b>Area Perhatian (Risiko):</b> Manajemen perlu menyusun strategi mitigasi risiko pada aspek 
                        <span class="weakness-tag">{weakness}</span>, dimana IUP ini memiliki nilai relatif lebih rendah dibandingkan kompetitor lainnya.</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.divider()
            with st.expander("📋 Lihat Tabel Peringkat Lengkap"):
                st.dataframe(hasil.style.background_gradient(cmap="Blues"), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
