import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
from logo import LOGO_PLN_B64

# ============================================================
# KONFIGURASI
# ============================================================
st.set_page_config(
    page_title="Antrian PLN ULP Rivai",
    page_icon="⚡",
    layout="wide"
)

ANTRIAN_FILE = "antrian.csv"
SURVEY_LINK  = "https://forms.gle/5yL8gq9TVgp2u9138"
KOLOM        = ["nomor","nama","jenis_layanan","tanggal","waktu_daftar","waktu_selesai","status"]

DAFTAR_LAYANAN = [
    "Permohonan Pasang Baru",
    "Perubahan Daya (Naik/Turun)",
    "Penyelesaian Pemutusan / Penyambungan Kembali",
    "Perubahan Nama / Balik Nama",
    "Pengaduan Tagihan Tidak Wajar",
    "Permohonan Subsidi / Listrik Bersubsidi",
    "Pengurusan Tunggakan Tagihan",
    "Komplain Meteran (Rusak, Segel, atau Tidak Akurat)",
    "Lainnya"
]

# ============================================================
# CSS
# ============================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

[data-testid="stAppViewContainer"] > .main {{ background-color: #f0f4fb; }}
[data-testid="block-container"] {{ padding-top: 0 !important; padding-left: 1rem !important; padding-right: 1rem !important; }}

h1,h2,h3 {{ color: #0a3d91 !important; font-weight: 600 !important; }}

[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background: #e8eef8;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    color: #4a6fa5 !important;
    padding: 8px 20px !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    background: #0a3d91 !important;
    color: white !important;
}}

[data-testid="stMetric"] {{
    background: white;
    border: 1px solid #dce6f5;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 4px rgba(10,61,145,0.06);
}}
[data-testid="stMetricValue"] {{ font-size:28px !important; font-weight:700 !important; color:#0a3d91 !important; }}
[data-testid="stMetricLabel"] {{ font-size:12px !important; color:#64748b !important; font-weight:500 !important; }}

.stFormSubmitButton > button {{
    background: #0a3d91 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px !important;
    width: 100% !important;
    transition: opacity 0.2s !important;
}}
.stFormSubmitButton > button:hover {{ opacity: 0.88 !important; }}
.stButton > button {{
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}}
.stDownloadButton > button {{
    background: white !important;
    color: #0a3d91 !important;
    border: 1.5px solid #0a3d91 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}

input, select {{ border-radius: 8px !important; }}
[data-testid="stDataFrame"] {{ border-radius: 10px !important; border: 1px solid #dce6f5 !important; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# FUNGSI DATA
# ============================================================
def load_antrian():
    if os.path.exists(ANTRIAN_FILE):
        df = pd.read_csv(ANTRIAN_FILE)
        # Pastikan kolom waktu_selesai ada (kompatibilitas data lama)
        if "waktu_selesai" not in df.columns:
            df["waktu_selesai"] = ""
        return df
    return pd.DataFrame(columns=KOLOM)

def save_antrian(df):
    df.to_csv(ANTRIAN_FILE, index=False)

def get_hari_ini():
    df = load_antrian()
    if df.empty:
        return df
    return df[df["tanggal"] == str(date.today())]

def nomor_berikutnya():
    df = get_hari_ini()
    if df.empty:
        return "A001"
    angka = int(df["nomor"].str[1:].astype(int).max()) + 1
    return f"A{angka:03d}"

def tambah_antrian(nama, jenis_layanan):
    df = load_antrian()
    nomor = nomor_berikutnya()
    baris = pd.DataFrame([{
        "nomor": nomor,
        "nama": nama,
        "jenis_layanan": jenis_layanan,
        "tanggal": str(date.today()),
        "waktu_daftar": datetime.now().strftime("%H:%M"),
        "waktu_selesai": "",
        "status": "Menunggu"
    }])
    df = pd.concat([df, baris], ignore_index=True)
    save_antrian(df)
    return nomor

def update_status(nomor, status_baru):
    df = load_antrian()
    df["waktu_selesai"] = df["waktu_selesai"].astype(str).replace("nan", "")
    mask = (df["nomor"] == nomor) & (df["tanggal"] == str(date.today()))
    df.loc[mask, "status"] = status_baru
    if status_baru == "Selesai":
        df.loc[mask, "waktu_selesai"] = datetime.now().strftime("%H:%M")
    save_antrian(df)

def get_antrian_aktif():
    df = get_hari_ini()
    if df.empty:
        return df
    return df[df["status"] == "Menunggu"].reset_index(drop=True)

def get_sedang_dilayani():
    df = get_hari_ini()
    if df.empty:
        return None
    dipanggil = df[df["status"] == "Dipanggil"]
    return dipanggil.iloc[-1] if not dipanggil.empty else None

# ============================================================
# SESSION STATE INIT
# ============================================================
if "tiket" not in st.session_state:
    st.session_state["tiket"] = None
if "form_key" not in st.session_state:
    st.session_state["form_key"] = 0

# ============================================================
# HEADER
# ============================================================
st.markdown(f"""
<div style="background:#0a3d91; border-radius:0 0 16px 16px; padding:16px 28px;
     display:flex; align-items:center; justify-content:space-between;
     margin-bottom:20px; margin-left:-1rem; margin-right:-1rem;">
  <div style="display:flex; align-items:center; gap:14px;">
    <img src="data:image/png;base64,{LOGO_PLN_B64}"
         style="width:52px; height:auto; border-radius:6px;">
    <div>
      <div style="font-size:18px; font-weight:700; color:white; line-height:1.2;">
        Sistem Antrian Digital
      </div>
      <div style="font-size:12px; color:#a8c4f0; margin-top:2px;">
        PLN ULP Rivai &nbsp;·&nbsp; Unit Layanan Pelanggan Palembang
      </div>
    </div>
  </div>
  <div style="text-align:right;">
    <div style="background:#FFC72C; border-radius:8px; padding:6px 14px;
         font-size:12px; font-weight:600; color:#0a3d91; display:inline-block;">
      {date.today().strftime("%A, %d %B %Y")}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# TAB UTAMA
# ============================================================
tab_pelanggan, tab_petugas = st.tabs(["👤  Pelanggan", "🧑‍💼  Petugas"])

# ============================================================
# TAB 1 — PELANGGAN
# ============================================================
with tab_pelanggan:

    if st.session_state["tiket"] is None:
        st.subheader("Ambil Nomor Antrian")
        st.write("Isi data di bawah untuk mendapatkan nomor antrian.")

        with st.form(key=f"form_antrian_{st.session_state['form_key']}", clear_on_submit=True):
            nama  = st.text_input("Nama Lengkap", placeholder="Masukkan nama lengkap Anda")
            jenis = st.selectbox("Keperluan", DAFTAR_LAYANAN)
            submit = st.form_submit_button("Ambil Nomor Antrian", use_container_width=True)

            if submit:
                if not nama.strip():
                    st.error("Nama wajib diisi.")
                else:
                    nomor = tambah_antrian(nama.strip(), jenis)
                    st.session_state["tiket"] = {
                        "nomor": nomor,
                        "nama": nama.strip(),
                        "jenis": jenis
                    }
                    st.rerun()

    else:
        tiket = st.session_state["tiket"]
        nomor = tiket["nomor"]

        df_hari = get_hari_ini()
        row_tiket = df_hari[df_hari["nomor"] == nomor]
        status_saat_ini = row_tiket.iloc[0]["status"] if not row_tiket.empty else "Menunggu"

        posisi = df_hari[
            (df_hari["status"] == "Menunggu") &
            (df_hari["nomor"] <= nomor)
        ].shape[0]

        st.markdown(f"""
        <div style="background:#0a3d91; border-radius:16px; padding:28px; text-align:center; margin:10px 0 16px 0;
             box-shadow: 0 4px 16px rgba(10,61,145,0.2);">
            <div style="font-size:12px; color:#a8c4f0; letter-spacing:1px; margin-bottom:8px;">NOMOR ANTRIAN ANDA</div>
            <div style="font-size:72px; font-weight:700; color:#FFC72C; line-height:1;">{nomor}</div>
            <div style="font-size:15px; color:#d4e4ff; margin-top:8px; font-weight:500;">{tiket['nama']}</div>
            <div style="font-size:12px; color:#8bafd8; margin-top:4px;">{tiket['jenis']}</div>
        </div>
        """, unsafe_allow_html=True)

        if status_saat_ini == "Menunggu":
            st.markdown(f"""
            <div style="background:#fff8e1; border:1px solid #FFC72C; border-radius:10px;
                 padding:12px 18px; text-align:center; margin-bottom:12px;">
                <span style="font-size:16px;">⏳</span>
                <span style="font-size:14px; color:#7a5c00; font-weight:500; margin-left:6px;">
                    Menunggu &nbsp;·&nbsp; <b>{posisi} orang</b> di depan Anda
                </span>
            </div>
            """, unsafe_allow_html=True)
            st.caption("Perbarui halaman untuk melihat status terbaru.")

        elif status_saat_ini == "Dipanggil":
            st.markdown("""
            <div style="background:#e8f5e9; border:1px solid #4caf50; border-radius:10px;
                 padding:14px 18px; text-align:center; margin-bottom:12px;">
                <span style="font-size:20px;">🔔</span>
                <span style="font-size:15px; color:#1b5e20; font-weight:600; margin-left:8px;">
                    Anda dipanggil! Silakan menuju loket pelayanan.
                </span>
            </div>
            """, unsafe_allow_html=True)

        elif status_saat_ini == "Selesai":
            st.markdown("""
            <div style="background:#e3f2fd; border:1px solid #2196f3; border-radius:10px;
                 padding:14px 18px; text-align:center; margin-bottom:16px;">
                <span style="font-size:20px;">✅</span>
                <span style="font-size:14px; color:#0d47a1; font-weight:500; margin-left:8px;">
                    Layanan selesai. Terima kasih telah mengunjungi PLN ULP Rivai!
                </span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background:white; border:1px solid #dce6f5; border-radius:12px; padding:18px; text-align:center; margin-bottom:12px;">
                <div style="font-size:15px; font-weight:600; color:#0a3d91; margin-bottom:6px;">Bagaimana layanan kami hari ini?</div>
                <div style="font-size:13px; color:#64748b; margin-bottom:14px;">Mohon luangkan waktu untuk mengisi survey singkat</div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button("Isi Survey Kepuasan Pelanggan", SURVEY_LINK, use_container_width=True)

        st.markdown("---")

        col_refresh, col_baru = st.columns(2)
        with col_refresh:
            if st.button("Perbarui Status", use_container_width=True):
                st.rerun()
        with col_baru:
            if st.button("Ambil Antrian Baru", use_container_width=True, type="primary"):
                st.session_state["tiket"] = None
                st.session_state["form_key"] += 1
                st.rerun()

    st.markdown("---")
    st.subheader("Cek Status Antrian")
    nomor_cek = st.text_input("Masukkan nomor antrian", placeholder="Contoh: A001", label_visibility="collapsed")

    if nomor_cek.strip():
        df_hari = get_hari_ini()
        baris = df_hari[df_hari["nomor"] == nomor_cek.strip().upper()]

        if baris.empty:
            st.warning("Nomor antrian tidak ditemukan untuk hari ini.")
        else:
            row = baris.iloc[0]
            warna = {"Menunggu": "#fff8e1", "Dipanggil": "#e8f5e9", "Selesai": "#e3f2fd"}
            border = {"Menunggu": "#FFC72C", "Dipanggil": "#4caf50", "Selesai": "#2196f3"}
            warna_teks = {"Menunggu": "#7a5c00", "Dipanggil": "#1b5e20", "Selesai": "#0d47a1"}
            s = row["status"]
            st.markdown(f"""
            <div style="background:{warna.get(s,'#f4f6fb')}; border:1px solid {border.get(s,'#dce6f5')};
                 border-radius:10px; padding:14px 18px; margin-top:8px;">
                <div style="font-size:20px; font-weight:700; color:#0a3d91;">{row['nomor']}</div>
                <div style="font-size:14px; font-weight:500; color:{warna_teks.get(s,'#1e3a6e')};">{row['nama']}</div>
                <div style="font-size:12px; color:#64748b; margin-top:2px;">{row['jenis_layanan']}</div>
                <div style="font-size:13px; font-weight:600; color:{warna_teks.get(s,'#1e3a6e')}; margin-top:8px;">Status: {s}</div>
            </div>
            """, unsafe_allow_html=True)

            if s == "Selesai":
                st.link_button("Isi Survey Kepuasan", SURVEY_LINK, use_container_width=True)

# ============================================================
# TAB 2 — PETUGAS
# ============================================================
with tab_petugas:
    st.subheader("Panel Petugas")

    df_hari  = get_hari_ini()
    total    = len(df_hari)
    menunggu = len(df_hari[df_hari["status"] == "Menunggu"]) if not df_hari.empty else 0
    selesai  = len(df_hari[df_hari["status"] == "Selesai"])  if not df_hari.empty else 0
    dilayani = get_sedang_dilayani()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Antrian Hari Ini", total)
    col2.metric("Menunggu", menunggu)
    col3.metric("Selesai Dilayani", selesai)

    st.markdown("---")

    if dilayani is not None:
        st.subheader("Sedang Dilayani")
        st.markdown(f"""
        <div style="background:#e8f5e9; border:1.5px solid #4caf50; border-radius:12px; padding:18px 22px;
             display:flex; align-items:center; gap:16px; margin-bottom:12px;">
            <div style="background:#0a3d91; border-radius:10px; width:56px; height:56px;
                 display:flex; align-items:center; justify-content:center;
                 font-size:20px; font-weight:700; color:#FFC72C; flex-shrink:0;">
                {dilayani['nomor']}
            </div>
            <div>
                <div style="font-size:17px; font-weight:600; color:#1b5e20;">{dilayani['nama']}</div>
                <div style="font-size:13px; color:#388e3c; margin-top:2px;">{dilayani['jenis_layanan']}</div>
                <div style="font-size:11px; color:#388e3c; margin-top:4px;">
                    ⏰ Jam Daftar: <b>{dilayani['waktu_daftar']}</b>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Tandai Selesai", type="primary", use_container_width=True):
            update_status(dilayani["nomor"], "Selesai")
            st.success(f"{dilayani['nomor']} — {dilayani['nama']} selesai dilayani pukul {datetime.now().strftime('%H:%M')}.")
            st.rerun()
    else:
        st.info("Tidak ada pelanggan yang sedang dilayani.")

    st.markdown("---")
    st.subheader("Antrian Menunggu")

    antrian_aktif = get_antrian_aktif()
    if antrian_aktif.empty:
        st.info("Tidak ada antrian yang menunggu saat ini.")
    else:
        for _, row in antrian_aktif.iterrows():
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"""
                <div style="background:white; border:1px solid #dce6f5; border-radius:10px;
                     padding:12px 16px; display:flex; align-items:center; gap:14px; margin-bottom:8px;">
                    <div style="background:#0a3d91; border-radius:8px; width:44px; height:44px;
                         display:flex; align-items:center; justify-content:center;
                         font-size:13px; font-weight:700; color:#FFC72C; flex-shrink:0;">
                        {row['nomor']}
                    </div>
                    <div>
                        <div style="font-size:14px; font-weight:500; color:#1e3a6e;">{row['nama']}</div>
                        <div style="font-size:12px; color:#64748b; margin-top:2px;">
                            {row['jenis_layanan']} &nbsp;·&nbsp; ⏰ Daftar: {row['waktu_daftar']}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                if dilayani is None:
                    if st.button("Panggil", key=f"panggil_{row['nomor']}", use_container_width=True, type="primary"):
                        update_status(row["nomor"], "Dipanggil")
                        st.success(f"Memanggil {row['nomor']} — {row['nama']}")
                        st.rerun()

    st.markdown("---")
    st.subheader("Riwayat Hari Ini")
    if df_hari.empty:
        st.caption("Belum ada data antrian hari ini.")
    else:
        # Tampilkan tabel dengan jam daftar dan jam selesai
        df_tampil = df_hari[["nomor","nama","jenis_layanan","waktu_daftar","waktu_selesai","status"]].copy()
        df_tampil.columns = ["Nomor","Nama","Keperluan","Jam Daftar","Jam Selesai","Status"]
        df_tampil["Jam Selesai"] = df_tampil["Jam Selesai"].fillna("").replace("", "-")
        st.dataframe(df_tampil, use_container_width=True, hide_index=True)

        csv = df_hari.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Download Rekap Hari Ini (CSV)", data=csv,
            file_name=f"antrian_{date.today()}.csv", mime="text/csv"
        )

    if st.button("Perbarui Data", use_container_width=True):
        st.rerun()
