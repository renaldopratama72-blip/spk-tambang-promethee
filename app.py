import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

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
        margin-top: 30px; margin-bottom: 30px;
    }
    .insight-title { font-weight: 800; color: #1e293b; font-size: 1.2rem; margin-bottom: 15px; }
    .insight-text { color: #475569; line-height: 1.7; font-size: 1.05rem; }
    
    /* Tags */
    .strength-tag { background: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.9em; }
    .weakness-tag { background: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.9em; }

    /* Metric Cards */
    .metric-card {
        background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eef0f2;
        text-align: center; transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    .metric-value { font-size: 2rem; font-weight: 800; color: #1e293b; }
    .metric-label { color: #64748b; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }

    /* Hero Winner */
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
# 2. CONFIG DATA & RUBRIK PENILAIAN
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

RUBRIK_PENILAIAN = {
    'C1': {'Low': 'Kapasitas Kecil (Cadangan Minim)', 'Mid': 'Kapasitas Sedang (5-10 Thn)', 'High': 'Kapasitas Besar (>10 Thn)'},
    'C2': {'Low': 'Sulit Dijual (Low Rank <3000)', 'Mid': 'Pasar Domestik (Std PLN)', 'High': 'Premium/Ekspor (>4500)'},
    'C3': {'Low': 'Rugi / Margin Negatif', 'Mid': 'Margin Tipis / Sensitif', 'High': 'Sangat Untung (High NPM)'},
    'C4': {'Low': 'Biaya MAHAL (Hauling Jauh)', 'Mid': 'Biaya WAJAR (Avg Industry)', 'High': 'Biaya MURAH (Efisien)'},
    'C5': {'Low': 'Rantai RUMIT (Double Handling)', 'Mid': 'Standar (Hambatan Minor)', 'High': 'SEDERHANA (Pit-to-port lancar)'},
    'C6': {'Low': 'Belum Ada / Bermasalah', 'Mid': 'Proses Berjalan', 'High': 'Lengkap (CnC)'},
    'C7': {'Low': 'Kompleks (SR Tinggi >10)', 'Mid': 'Ekonomis (SR 5-8)', 'High': 'Sangat Baik (SR <4)'},
    'C8': {'Low': 'Hutan Lindung / Konflik', 'Mid': 'Butuh Izin Khusus', 'High': 'Area Putih (APL)'},
    'C9': {'Low': 'Pencemaran Tinggi', 'Mid': 'Terdampak Sedang', 'High': 'Aman / Jauh Pemukiman'},
    'C10': {'Low': 'Konflik / Demo Warga', 'Mid': 'Kondusif (Berbayar)', 'High': 'Sangat Mendukung'},
    'C11': {'Low': 'Amdal Belum Ada', 'Mid': 'Dalam Revisi', 'High': 'Amdal Lengkap'},
    'C12': {'Low': 'Baru Merintis', 'Mid': 'Pemain Lama', 'High': 'Market Leader'},
    'C13': {'Low': 'Tidak Jelas / Spekulatif', 'Mid': 'Ada tapi Belum Detail', 'High': 'Matang & Terstruktur'},
    'C14': {'Low': 'Tidak Dikenal', 'Mid': 'Relasi Biasa', 'High': 'Relasi Kuat / Strategis'}
}

def get_rubrik_df():
    data = []
    for kode, desc in RUBRIK_PENILAIAN.items():
        data.append({
            "Kode": kode,
            "Kriteria": KRITERIA_CONFIG[kode]['nama'],
            "🔴 Rendah (0-49)": desc['Low'],
            "🟡 Sedang (50-75)": desc['Mid'],
            "🟢 Tinggi (76-99)": desc['High']
        })
    return pd.DataFrame(data)

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
# 4. SIDEBAR NAVIGATION (FIXED)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040504.png", width=70)
    st.markdown("### SPK Tambang")
    
    # ⚠️ BAGIAN KRUSIAL UNTUK PINDAH HALAMAN
    # Kita beri nama key="main_nav". Ini agar tombol bisa mengubah nilai navigasi ini.
    if 'main_nav' not in st.session_state:
        st.session_state['main_nav'] = 'Dashboard'

    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Input Data", "Panduan Nilai"],
        icons=["speedometer2", "keyboard", "journal-check"],
        default_index=0,
        key="main_nav", # <--- INI KUNCINYA. Key menghubungkan menu dengan Session State.
        styles={
            "container": {"padding": "0!important", "background-color": "#f0f2f6"},
            "icon": {"color": "#2563eb", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#e2e8f0"},
            "nav-link-selected": {"background-color": "#2563eb"},
        }
    )
    
    st.divider()
    
    st.markdown("**📂 Metode Input Data**")
    input_method = st.radio("Pilih Sumber:", ["Upload Excel", "Input Manual / Edit"], label_visibility="collapsed")
    
    uploaded_file = None
    if input_method == "Upload Excel":
        uploaded_file = st.file_uploader("File .xlsx", type=['xlsx'])
    
    st.divider()
    st.caption("Developed by **Renaldo Pratama**\nMM Universitas Bakrie")

# ==========================================
# 5. HALAMAN UTAMA
# ==========================================

# --- INISIALISASI SESSION STATE ---
if 'df_input' not in st.session_state:
    default_cols = ['Nama IUP'] + list(KRITERIA_CONFIG.keys())
    st.session_state.df_input = pd.DataFrame(columns=default_cols)

# Logika Load Data
if input_method == "Upload Excel" and uploaded_file is not None:
    try:
        temp_df = pd.read_excel(uploaded_file)
        st.session_state.df_input = temp_df
    except:
        st.error("File tidak valid")
elif input_method == "Input Manual / Edit" and st.session_state.df_input.empty:
    dummy_data = {'Nama IUP': ['IUP A', 'IUP B', 'IUP C']}
    for k in KRITERIA_CONFIG.keys():
        dummy_data[k] = [0, 0, 0] 
    st.session_state.df_input = pd.DataFrame(dummy_data)


# --- HALAMAN: PANDUAN NILAI ---
if selected == "Panduan Nilai":
    st.title("📖 Panduan Parameter Penilaian (0-100)")
    st.markdown("""
    Gunakan tabel di bawah ini sebagai acuan saat mengisi skor pada menu **Input Data**.
    Rentang nilai dibagi menjadi 3 kategori: **Rendah (0-49)**, **Menengah (50-75)**, dan **Tinggi (76-99)**.
    """)
    
    df_rubrik = get_rubrik_df()
    st.dataframe(
        df_rubrik, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Kode": st.column_config.TextColumn("Kode", width="small"),
            "🔴 Rendah (0-49)": st.column_config.TextColumn("Rendah (Buruk)", width="medium"),
            "🟢 Tinggi (76-99)": st.column_config.TextColumn("Tinggi (Baik/Ideal)", width="medium"),
        }
    )
    st.info("💡 **Tips:** Semakin tinggi skor, semakin 'Ideal' kondisi tersebut menurut preferensi perusahaan.")


# --- HALAMAN: INPUT DATA (AUTO REDIRECT FIX) ---
elif selected == "Input Data":
    st.title("📝 Input & Edit Data")
    st.markdown("Anda bisa mengubah angka di tabel bawah ini secara langsung untuk melakukan simulasi.")
    
    # === POP UP PANDUAN ===
    with st.expander("📖 Buka Panduan Penilaian (Contekan)", expanded=False):
        st.info("👇 **Panduan Pengisian Skor (0-100)**. Klik header kolom untuk mengurutkan.")
        df_popup = get_rubrik_df()
        st.dataframe(df_popup, use_container_width=True, hide_index=True, height=300)
    
    # === EDITOR UTAMA ===
    st.markdown("### Tabel Input")
    col_input, col_info = st.columns([3, 1])
    
    with col_input:
        edited_df = st.data_editor(
            st.session_state.df_input,
            num_rows="dynamic",
            use_container_width=True,
            height=450,
            key="editor"
        )
        st.session_state.df_input = edited_df

    with col_info:
        st.warning("⚠️ **Perhatian**")
        st.markdown("""
        1. **Kolom C1-C14**: Isi angka 0-100.
        2. **Gunakan Panduan** jika bingung.
        """)
        
        # === TOMBOL SIMPAN & PINDAH HALAMAN ===
        if st.button("💾 Simpan & Lihat Dashboard ➡️", type="primary"):
            # 1. Simpan data (Data editor otomatis tersimpan ke session, kita tegaskan saja)
            st.session_state.df_input = edited_df
            
            # 2. UBAH NAVIGASI KE DASHBOARD SECARA PAKSA
            st.session_state["main_nav"] = "Dashboard"
            
            # 3. RELOAD APLIKASI
            st.rerun()


# --- HALAMAN: DASHBOARD ---
elif selected == "Dashboard":
    df_to_process = st.session_state.df_input.copy()
    
    if df_to_process.empty or len(df_to_process) < 2:
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image(
                "https://images.squarespace-cdn.com/content/v1/5acda2f4c258b4bd2d14dca2/1653447668933-C9BBM4LAGE1BBEINI7FP/Perusahaan+Tambang+di+Bursa+Efek+Indonesia.jpg?format=2500w",
                caption="Sektor Pertambangan Indonesia", use_container_width=True
            )
            st.info("👈 Data masih kosong. Silakan ke menu **Input Data** untuk mengisi nilai.")
            
    else:
        try:
            df_to_process = df_to_process.set_index(df_to_process.columns[0])
            wajib = list(KRITERIA_CONFIG.keys())
            kurang = [c for c in wajib if c not in df_to_process.columns]
            
            if kurang:
                st.error(f"❌ Data belum lengkap. Kolom hilang: {kurang}")
            else:
                hasil = hitung_promethee(df_to_process)
                best_mine = hasil.index[0]
                best_score = hasil.iloc[0]['Net Flow']
                strengths, weakness = generate_insight(df_to_process, best_mine)
                
                # Parameter
                st.subheader("1. Parameter & Konfigurasi Model")
                with st.expander("ℹ️ Lihat Detail Bobot & Threshold", expanded=False):
                    param_data = []
                    for k, v in KRITERIA_CONFIG.items():
                        param_data.append({
                            "Kode": k, "Nama": v['nama'], "Tipe": v['tipe'].upper(),
                            "Bobot": f"{v['bobot']:.4f}", "Q": v['q'], "P": v['p']
                        })
                    st.dataframe(pd.DataFrame(param_data), use_container_width=True, hide_index=True)

                st.divider()
                st.subheader("2. Hasil Analisis Keputusan")

                # Hero
                st.markdown(f"""
                <div class="hero-winner">
                    <div class="hero-title">REKOMENDASI KEPUTUSAN TERBAIK</div>
                    <div class="hero-name">{best_mine}</div>
                    <div style="font-size: 1.2rem; margin-top: 10px;">
                        💎 Skor Net Flow: <b>{best_score:.4f}</b> | Status: <span style="background: #2ecc71; padding: 2px 10px; border-radius: 5px; font-size: 0.9rem;">Sangat Direkomendasikan</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # KPI
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f"<div class='metric-card'><div class='metric-value'>{len(df_to_process)}</div><div class='metric-label'>Alternatif</div></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#2563eb;'>{hasil.iloc[1]['Net Flow']:.3f}</div><div class='metric-label'>Runner Up ({hasil.index[1]})</div></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#e11d48;'>{hasil.iloc[-1]['Net Flow']:.3f}</div><div class='metric-label'>Terendah ({hasil.index[-1]})</div></div>", unsafe_allow_html=True)
                gap = best_score - hasil.iloc[1]['Net Flow']
                with c4: st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#10b981;'>+{gap:.3f}</div><div class='metric-label'>Gap Kemenangan</div></div>", unsafe_allow_html=True)

                st.write("<br>", unsafe_allow_html=True)

                # Charts
                col1, col2 = st.columns([1.5, 1])
                with col1:
                    st.subheader("📊 Peringkat Performa")
                    df_chart = hasil.reset_index()
                    df_chart.columns = ['Alternatif', 'Net Flow', 'Leaving', 'Entering']
                    df_chart['Warna'] = ['#0f172a' if x == best_mine else '#94a3b8' for x in df_chart['Alternatif']]
                    fig = px.bar(df_chart, y='Alternatif', x='Net Flow', orientation='h', text_auto='.3f', color='Alternatif', color_discrete_sequence=df_chart['Warna'].tolist())
                    fig.update_layout(showlegend=False, height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("🕸️ Profil Juara")
                    winner_vals = ((df_to_process - df_to_process.min()) / (df_to_process.max() - df_to_process.min())).loc[best_mine].tolist()
                    fig_radar = go.Figure(go.Scatterpolar(r=winner_vals, theta=df_to_process.columns.tolist(), fill='toself', name=best_mine))
                    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False, height=400, margin=dict(l=40, r=40, t=20, b=20))
                    st.plotly_chart(fig_radar, use_container_width=True)

                # Insight Box
                st.write("<br>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="insight-box">
                    <div class="insight-title">Catatan & Rekomendasi untuk Manajemen</div>
                    <div class="insight-text">
                        Berdasarkan hasil analisis, <b>{best_mine}</b> terpilih sebagai opsi paling optimal.
                        <br><br>
                        <ul>
                            <li><b>Keunggulan Kompetitif:</b> Unggul pada aspek <span class="strength-tag">{strengths[0]}</span>, <span class="strength-tag">{strengths[1]}</span>, dan <span class="strength-tag">{strengths[2]}</span>.</li>
                            <br>
                            <li><b>Area Perhatian:</b> Perlu mitigasi risiko pada aspek <span class="weakness-tag">{weakness}</span>.</li>
                        </ul>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.divider()
                with st.expander("📋 Lihat Tabel Lengkap"):
                    st.dataframe(hasil.style.background_gradient(cmap="Blues"), use_container_width=True)

        except Exception as e:
            st.error(f"Error Proses: {e}")
