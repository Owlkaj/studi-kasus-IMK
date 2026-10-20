"""
Dashboard Eksekutif Pemantauan Fluktuasi Harga Pangan & Deteksi Dini Inflasi Daerah
Studi Kasus: Dinas Ketahanan Pangan Provinsi Bengkulu

Tugas kuliah: Human-Computer Interaction (HCI) & Data Visualization.

Prinsip yang diterapkan (ringkas, detail di README.md dan tab dokumentasi):
  - User-Centered Design  : User Persona "Ibu Ratna" (Kabid Distribusi Pangan)
  - Cognitive Load Theory : KPI ringkas, detail disembunyikan (tooltip / expander)
  - Preattentive Attrib.  : biru-abu untuk normal, MERAH hanya untuk > +15% di atas HET
  - Gestalt               : proximity, similarity, figure-ground, continuity, closure
  - Tufte                 : data-ink ratio tinggi, tanpa chartjunk
  - Shneiderman's Mantra  : Overview first -> Zoom & filter -> Details-on-demand
  - 10 Heuristik Nielsen  : status sistem, kontrol pengguna (Reset Filter), dll.

Catatan: seluruh data adalah DATA SIMULASI (sintetis) untuk keperluan akademik.

Jalankan dengan:  streamlit run app_dashboard_hci.py
"""

from __future__ import annotations

import inspect
from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# 1. KONSTANTA & KONFIGURASI
# =============================================================================
SEED = 2026
HARI = 90                  # jumlah hari data historis
KRITIS_PCT = 15.0          # ambang kritis: > 15% di atas HET
WASPADA_PCT = 5.0          # ambang waspada: > 5% di atas HET
STOK_AMAN = 0.90           # rasio stok >= 90% dari normal -> "Aman"
STOK_MENIPIS = 0.75        # rasio stok >= 75% -> "Menipis", di bawahnya "Defisit"

# Palet warna (Preattentive Attributes: hanya SATU warna "alarm" = merah menyala)
WARNA_NORMAL = "#7F9CC0"       # biru keabuan lembut -> data normal
WARNA_BIRU_TUA = "#2F5D8C"     # biru tegas -> garis rata-rata / fokus
WARNA_ABU = "#C3CAD5"          # abu lembut -> konteks (latar / figure-ground)
WARNA_ABU_TUA = "#4A5568"      # abu tua -> garis acuan HET
WARNA_KRITIS = "#FF1F1F"       # MERAH MENYALA -> melampaui ambang kritis
WARNA_TEKS = "#2D3748"

# Komoditas: satuan, HET/HAP ilustratif (Rp), volatilitas harian, stok dasar per pasar (ton)
KOMODITAS = {
    "Beras":         dict(satuan="kg",    het=12500, vol=0.004, stok=85.0),
    "Cabai Merah":   dict(satuan="kg",    het=45000, vol=0.020, stok=4.5),
    "Bawang Merah":  dict(satuan="kg",    het=38000, vol=0.012, stok=7.0),
    "Minyak Goreng": dict(satuan="liter", het=15700, vol=0.003, stok=22.0),
    "Telur Ayam":    dict(satuan="kg",    het=30000, vol=0.008, stok=14.0),
    "Daging Ayam":   dict(satuan="kg",    het=40000, vol=0.008, stok=12.0),
}

# Wilayah / pasar acuan (ilustratif): faktor harga (h) dan skala stok (s)
WILAYAH = {
    "Kota Bengkulu":    dict(pasar="Pasar Panorama",    h=1.03, s=1.50),
    "Rejang Lebong":    dict(pasar="Pasar Curup",       h=0.99, s=1.00),
    "Bengkulu Utara":   dict(pasar="Pasar Arga Makmur", h=1.00, s=1.10),
    "Bengkulu Selatan": dict(pasar="Pasar Manna",       h=1.02, s=0.80),
    "Kepahiang":        dict(pasar="Pasar Kepahiang",   h=0.98, s=0.70),
}

# Skenario lonjakan harga (storyline data): (wilayah, komoditas) -> (hari_mulai, durasi, amplitudo)
SKENARIO_LONJAKAN = {
    ("Kota Bengkulu", "Cabai Merah"):      (60, 46, 0.52),
    ("Bengkulu Utara", "Cabai Merah"):     (64, 40, 0.44),
    ("Rejang Lebong", "Cabai Merah"):      (48, 34, 0.26),
    ("Bengkulu Selatan", "Bawang Merah"):  (58, 44, 0.30),
    ("Kota Bengkulu", "Bawang Merah"):     (70, 30, 0.22),
    ("Kepahiang", "Minyak Goreng"):        (45, 50, 0.19),
    ("Bengkulu Utara", "Telur Ayam"):      (66, 40, 0.27),
    ("Kota Bengkulu", "Daging Ayam"):      (62, 40, 0.19),
    ("Kepahiang", "Beras"):                (55, 40, 0.10),
}

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}


# =============================================================================
# 2. UTILITAS FORMAT (Nielsen #2: Match between system and the real world)
#    Format angka Indonesia: titik sebagai pemisah ribuan, koma sebagai desimal.
# =============================================================================
def stretch(fn) -> dict:
    """Kompatibilitas lintas versi Streamlit untuk lebar penuh (width vs use_container_width)."""
    try:
        if "width" in inspect.signature(fn).parameters:
            return {"width": "stretch"}
    except (TypeError, ValueError):
        pass
    return {"use_container_width": True}


def fmt_num(x: float, desimal: int = 0) -> str:
    s = f"{x:,.{desimal}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_rp(x: float) -> str:
    return "Rp " + fmt_num(x)


def fmt_pct(x: float) -> str:
    if round(x, 1) == 0:
        x = 0.0
    s = fmt_num(x, 1)
    return ("+" + s if x > 0 else s) + "%"


def fmt_stok(x: float) -> str:
    return fmt_num(x, 2 if x < 10 else 1) + " ton"


def fmt_tgl(ts: pd.Timestamp) -> str:
    return f"{ts.day} {BULAN[ts.month - 1]} {ts.year}"


def rekomendasi(pct: float, stok_rasio: float) -> str:
    """Rekomendasi tindakan - hanya muncul saat hover (Details-on-Demand)."""
    if pct > KRITIS_PCT:
        if stok_rasio < STOK_MENIPIS:
            return "Segera gelar operasi pasar & tambah pasokan"
        return "Segera gelar operasi pasar & koordinasi distributor"
    if pct > WASPADA_PCT:
        return "Pantau harian & siapkan stok cadangan"
    return "Normal: pemantauan rutin"


# =============================================================================
# 3. GENERATOR DATASET SINTETIS
# =============================================================================
def _bentuk_lonjakan(hari: int, mulai: int, durasi: int) -> np.ndarray:
    """Kurva lonjakan halus (0..1) berbentuk sin^2; terpotong jika melewati akhir data."""
    s = np.zeros(hari)
    idx = np.arange(mulai, min(mulai + durasi, hari))
    if len(idx):
        s[idx] = np.sin(np.pi * (idx - mulai + 0.5) / durasi) ** 2
    return s


def _ar1(rng: np.random.Generator, n: int, phi: float, sd: float) -> np.ndarray:
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + rng.normal(0, sd)
    return x


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Tambahkan kolom turunan: selisih HET, status, rasio stok, rekomendasi, dan teks hover."""
    df = df.copy()
    df["selisih_rp"] = df["harga"] - df["het"]
    df["selisih_pct"] = df["selisih_rp"] / df["het"] * 100
    df["status"] = np.select(
        [df["selisih_pct"] > KRITIS_PCT, df["selisih_pct"] > WASPADA_PCT],
        ["Kritis", "Waspada"],
        default="Normal",
    )
    median_stok = df.groupby(["wilayah", "komoditas"])["stok_ton"].transform("median")
    df["stok_rasio"] = df["stok_ton"] / median_stok
    df["tindakan"] = [rekomendasi(p, r) for p, r in zip(df["selisih_pct"], df["stok_rasio"])]

    # Kolom teks siap tampil untuk tooltip
    df["harga_fmt"] = [f"{fmt_rp(h)}/{s}" for h, s in zip(df["harga"], df["satuan"])]
    df["het_fmt"] = [f"{fmt_rp(h)}/{s}" for h, s in zip(df["het"], df["satuan"])]
    df["selisih_fmt"] = [f"{'+' if r > 0 else ''}{fmt_rp(r)} ({fmt_pct(p)})"
                         for r, p in zip(df["selisih_rp"], df["selisih_pct"])]
    df["stok_fmt"] = [fmt_stok(x) for x in df["stok_ton"]]
    df["tanggal_fmt"] = [fmt_tgl(t) for t in df["tanggal"]]
    return df


@st.cache_data(show_spinner=False)
def generate_dataset(seed: int = SEED, hari: int = HARI, anchor: str = "") -> pd.DataFrame:
    """
    Generator dataset realistis: 6 komoditas x 5 wilayah x 90 hari.
    Kolom: tanggal, wilayah, pasar, komoditas, satuan, harga (Rp), het (Rp), stok_ton.
    Harga = HET x faktor wilayah x (rasio dasar + fluktuasi AR(1) + lonjakan skenario).
    Stok turun saat lonjakan harga (hubungan pasokan-harga yang kemudian dicek lewat scatter plot).
    `anchor` (tanggal hari ini) ikut menjadi kunci cache agar data bergeser tiap hari.
    """
    rng = np.random.default_rng(seed)
    akhir = pd.Timestamp(anchor).normalize() if anchor else pd.Timestamp.today().normalize()
    tanggal = pd.date_range(end=akhir, periods=hari, freq="D")
    potongan = []

    for w, wcfg in WILAYAH.items():
        for k, kcfg in KOMODITAS.items():
            if (w, k) in SKENARIO_LONJAKAN:
                mulai, durasi, amp = SKENARIO_LONJAKAN[(w, k)]
                amp = amp * rng.uniform(0.95, 1.05)
            elif rng.random() < 0.25:  # lonjakan kecil acak agar data tidak terlalu "rapi"
                mulai = int(rng.integers(10, 60))
                durasi = int(rng.integers(15, 30))
                amp = float(rng.uniform(0.03, 0.07))
            else:
                mulai, durasi, amp = 0, 1, 0.0

            bentuk = _bentuk_lonjakan(hari, mulai, durasi)
            fluktuasi = _ar1(rng, hari, 0.92, kcfg["vol"])
            harga = kcfg["het"] * wcfg["h"] * (0.95 + fluktuasi + amp * bentuk)
            harga = np.round(harga / 100) * 100

            penurunan = min(0.6, 1.6 * amp) * bentuk
            noise = _ar1(rng, hari, 0.8, 0.03)
            stok_dasar = kcfg["stok"] * wcfg["s"]
            stok = np.clip(stok_dasar * (1 - penurunan + noise), 0.1 * stok_dasar, None)

            potongan.append(pd.DataFrame({
                "tanggal": tanggal,
                "wilayah": w,
                "pasar": wcfg["pasar"],
                "komoditas": k,
                "satuan": kcfg["satuan"],
                "harga": harga,
                "het": float(kcfg["het"]),
                "stok_ton": np.round(stok, 2),
            }))

    df = pd.concat(potongan, ignore_index=True)
    return enrich(df)


# =============================================================================
# 4. PERHITUNGAN KPI  (OVERVIEW FIRST)
# =============================================================================
def hitung_kpi(d: pd.DataFrame, df_full: pd.DataFrame) -> dict:
    tgl_akhir = d["tanggal"].max()
    akhir = d[d["tanggal"] == tgl_akhir]

    # KPI 1 - Komoditas berstatus kritis (di tanggal terakhir, minimal di satu pasar)
    krit = akhir[akhir["selisih_pct"] > KRITIS_PCT]
    n_kom_krit = krit["komoditas"].nunique()
    n_kom = akhir["komoditas"].nunique()
    n_kombinasi_krit = len(krit)

    # KPI 2 - Rata-rata perubahan harga (rata-rata 7 hari terakhir vs 7 hari pertama periode)
    perubahan = []
    for _, g in d.groupby(["wilayah", "komoditas"]):
        g = g.sort_values("tanggal")
        k = max(1, min(7, len(g) // 2))
        awal, akh = g["harga"].iloc[:k].mean(), g["harga"].iloc[-k:].mean()
        perubahan.append((akh / awal - 1) * 100)
    rata_perubahan = float(np.mean(perubahan))

    # KPI 3 - Wilayah prioritas operasi pasar
    per_wilayah = (
        akhir.groupby("wilayah")
        .agg(n_krit=("selisih_pct", lambda s: int((s > KRITIS_PCT).sum())),
             rata_pct=("selisih_pct", "mean"))
        .sort_values(["n_krit", "rata_pct"], ascending=False)
    )
    wilayah_top = per_wilayah.index[0]
    n_krit_top = int(per_wilayah.iloc[0]["n_krit"])
    pct_top = float(per_wilayah.iloc[0]["rata_pct"])

    # KPI 4 - Status ketersediaan stok (3 hari terakhir vs median 90 hari tiap pasar-komoditas)
    basis = df_full.groupby(["wilayah", "komoditas"])["stok_ton"].median()
    tiga = (d[d["tanggal"] >= tgl_akhir - pd.Timedelta(days=2)]
            .groupby(["wilayah", "komoditas"])["stok_ton"].mean())
    rasio_seri = tiga / basis.loc[tiga.index]
    rasio = float(rasio_seri.mean())
    n_tipis = int((rasio_seri < STOK_MENIPIS).sum())
    if rasio >= STOK_AMAN:
        status_stok = "Aman"
    elif rasio >= STOK_MENIPIS:
        status_stok = "Menipis"
    else:
        status_stok = "Defisit"

    return dict(
        tgl_akhir=tgl_akhir, n_kom_krit=n_kom_krit, n_kom=n_kom, n_kombinasi_krit=n_kombinasi_krit,
        rata_perubahan=rata_perubahan, wilayah_top=wilayah_top, n_krit_top=n_krit_top, pct_top=pct_top,
        rasio=rasio, status_stok=status_stok, n_tipis=n_tipis, n_seri=len(rasio_seri),
    )


# =============================================================================
# 5. GRAFIK  (Pemilihan grafik tepat + Tufte's Data-Ink Ratio)
# =============================================================================
HOVER_COLS = ["wilayah", "pasar", "harga_fmt", "het_fmt", "selisih_fmt",
              "tanggal_fmt", "stok_fmt", "tindakan"]
HOVER_TEMPLATE = (
    "<b>%{customdata[0]}</b> &middot; %{customdata[1]}<br>"
    "%{customdata[5]}<br>"
    "Harga: <b>%{customdata[2]}</b> (HET %{customdata[3]})<br>"
    "Selisih HET: <b>%{customdata[4]}</b><br>"
    "Stok: %{customdata[6]}<br>"
    "<i>Tindakan: %{customdata[7]}</i><extra></extra>"
)


def _tata_letak_dasar(fig: go.Figure, tinggi: int) -> go.Figure:
    """Tufte: hapus grid, border, legenda, dan dekorasi; sisakan data & label penting."""
    fig.update_layout(
        template="simple_white",
        height=tinggi,
        margin=dict(l=10, r=20, t=10, b=10),
        showlegend=False,
        hovermode="closest",
        hoverlabel=dict(bgcolor="white", font_size=12, font_color=WARNA_TEKS, align="left"),
        font=dict(color=WARNA_TEKS, size=12),
        separators=",.",  # desimal koma, ribuan titik
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def grafik_tren(df_k: pd.DataFrame, satuan: str) -> go.Figure:
    """Line chart bersih: tren harga harian terhadap garis HET (Gestalt: continuity)."""
    het = float(df_k["het"].iloc[0])
    ambang = het * (1 + KRITIS_PCT / 100)
    banyak_wilayah = df_k["wilayah"].nunique() > 1
    fig = go.Figure()

    # Garis tiap wilayah: abu lembut sebagai konteks (figure-ground), biru bila hanya satu wilayah
    for _, g in df_k.groupby("wilayah"):
        fig.add_trace(go.Scatter(
            x=g["tanggal"], y=g["harga"], mode="lines",
            line=dict(color=WARNA_ABU if banyak_wilayah else WARNA_BIRU_TUA,
                      width=1.3 if banyak_wilayah else 2.6),
            customdata=g[HOVER_COLS].to_numpy(), hovertemplate=HOVER_TEMPLATE,
        ))

    # Garis rata-rata wilayah terpilih sebagai "figure" utama
    if banyak_wilayah:
        rata = df_k.groupby("tanggal").agg(harga=("harga", "mean")).reset_index()
        rata["pct"] = (rata["harga"] / het - 1) * 100
        teks = [
            f"<b>Rata-rata wilayah terpilih</b><br>{fmt_tgl(t)}<br>"
            f"Harga: <b>{fmt_rp(h)}/{satuan}</b><br>Selisih HET: <b>{fmt_pct(p)}</b><extra></extra>"
            for t, h, p in zip(rata["tanggal"], rata["harga"], rata["pct"])
        ]
        fig.add_trace(go.Scatter(
            x=rata["tanggal"], y=rata["harga"], mode="lines",
            line=dict(color=WARNA_BIRU_TUA, width=3), hovertemplate=teks,
        ))

    # Titik MERAH MENYALA otomatis pada data > +15% di atas HET (Preattentive: hue)
    krit = df_k[df_k["selisih_pct"] > KRITIS_PCT]
    if not krit.empty:
        fig.add_trace(go.Scatter(
            x=krit["tanggal"], y=krit["harga"], mode="markers",
            marker=dict(color=WARNA_KRITIS, size=7),
            customdata=krit[HOVER_COLS].to_numpy(), hovertemplate=HOVER_TEMPLATE,
        ))

    # Garis acuan dengan label langsung (tanpa legenda)
    fig.add_hline(y=het, line=dict(color=WARNA_ABU_TUA, width=1.5, dash="dash"),
                  annotation_text=f"HET {fmt_rp(het)}", annotation_position="top left",
                  annotation_font=dict(size=11, color=WARNA_ABU_TUA))
    fig.add_hline(y=ambang, line=dict(color=WARNA_ABU_TUA, width=1, dash="dot"),
                  annotation_text=f"Ambang kritis (+{KRITIS_PCT:.0f}%)", annotation_position="top left",
                  annotation_font=dict(size=11, color=WARNA_ABU_TUA))

    # Sumbu X dengan label bulan Indonesia
    tanggal = np.sort(df_k["tanggal"].unique())
    pos = np.unique(np.linspace(0, len(tanggal) - 1, min(7, len(tanggal))).astype(int))
    tickvals = pd.to_datetime(tanggal[pos])
    fig.update_xaxes(tickvals=tickvals, ticktext=[f"{t.day} {BULAN[t.month - 1]}" for t in tickvals])
    lo = min(df_k["harga"].min(), het) * 0.94
    hi = max(df_k["harga"].max(), ambang) * 1.06
    fig.update_yaxes(range=[lo, hi], tickformat=",d", title=f"Harga (Rp/{satuan})")
    return _tata_letak_dasar(fig, 400)


def grafik_selisih(df_last: pd.DataFrame) -> go.Figure:
    """Horizontal bar: selisih harga terhadap HET antar wilayah (merah bila > +15%)."""
    g = df_last.sort_values("selisih_pct")  # nilai terbesar tampil di atas
    warna = [WARNA_KRITIS if v > KRITIS_PCT else WARNA_NORMAL for v in g["selisih_pct"]]
    fig = go.Figure(go.Bar(
        x=g["selisih_pct"], y=g["wilayah"], orientation="h",
        marker_color=warna, text=[fmt_pct(v) for v in g["selisih_pct"]],
        textposition="outside", cliponaxis=False, textfont=dict(size=12, color=WARNA_TEKS),
        customdata=g[HOVER_COLS].to_numpy(), hovertemplate=HOVER_TEMPLATE,
    ))
    fig.add_vline(x=0, line=dict(color=WARNA_ABU_TUA, width=1))
    fig.add_vline(x=KRITIS_PCT, line=dict(color=WARNA_ABU_TUA, width=1, dash="dot"),
                  annotation_text=f"+{KRITIS_PCT:.0f}%", annotation_position="top",
                  annotation_font=dict(size=11, color=WARNA_ABU_TUA))
    xmin = min(0.0, g["selisih_pct"].min()) - 4
    xmax = max(KRITIS_PCT, g["selisih_pct"].max()) * 1.25 + 2
    fig.update_xaxes(range=[xmin, xmax], ticksuffix="%", tickformat=".0f",
                     title="Selisih terhadap HET (0% = tepat di HET)")
    fig.update_yaxes(title=None)
    fig.update_layout(bargap=0.35)
    return _tata_letak_dasar(fig, 340)


def grafik_scatter(df_k: pd.DataFrame, satuan: str) -> tuple[go.Figure, float | None]:
    """Scatter plot: korelasi stok pasokan (ton) vs harga (Rp)."""
    fig = go.Figure()
    normal = df_k[df_k["selisih_pct"] <= KRITIS_PCT]
    krit = df_k[df_k["selisih_pct"] > KRITIS_PCT]
    for dset, warna, ukuran, opa in ((normal, WARNA_NORMAL, 6, 0.55), (krit, WARNA_KRITIS, 8, 0.95)):
        if dset.empty:
            continue
        fig.add_trace(go.Scatter(
            x=dset["stok_ton"], y=dset["harga"], mode="markers",
            marker=dict(color=warna, size=ukuran, opacity=opa),
            customdata=dset[HOVER_COLS].to_numpy(), hovertemplate=HOVER_TEMPLATE,
        ))

    r = None
    x, y = df_k["stok_ton"].to_numpy(), df_k["harga"].to_numpy()
    if len(df_k) >= 3 and np.std(x) > 0 and np.std(y) > 0:
        r = float(np.corrcoef(x, y)[0, 1])
        koef = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 20)
        fig.add_trace(go.Scatter(x=xs, y=np.polyval(koef, xs), mode="lines", hoverinfo="skip",
                                 line=dict(color=WARNA_ABU_TUA, width=1.5, dash="dash")))
    fig.update_xaxes(title="Stok pasokan (ton)")
    fig.update_yaxes(title=f"Harga (Rp/{satuan})", tickformat=",d")
    return _tata_letak_dasar(fig, 340), r


def tafsir_korelasi(r: float) -> str:
    a = abs(r)
    kekuatan = "sangat kuat" if a >= 0.8 else "kuat" if a >= 0.6 else "sedang" if a >= 0.4 else "lemah"
    arah = "negatif: stok turun, harga cenderung naik" if r < 0 else "positif"
    return f"r = {fmt_num(r, 2)} ({kekuatan}, {arah})"


# =============================================================================
# 6. KOMPONEN ANTARMUKA
# =============================================================================
CSS = """
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
.kpi {background:#F7F9FC; border:1px solid #E2E8F0; border-left:6px solid #7F9CC0;
      border-radius:8px; padding:14px 16px; min-height:122px;}
.kpi-kritis {background:#FFF5F5; border-color:#FED7D7; border-left-color:#FF1F1F;}
.kpi-label {font-size:0.82rem; color:#4A5568; font-weight:600; letter-spacing:.2px;}
.kpi-value {font-size:1.85rem; color:#1A202C; font-weight:700; line-height:1.25; margin:2px 0;}
.kpi-kritis .kpi-value {color:#FF1F1F;}
.kpi-sub {font-size:0.8rem; color:#4A5568;}
.langkah {font-size:0.78rem; font-weight:700; color:#2F5D8C; text-transform:uppercase; letter-spacing:.8px;}
</style>
"""


def render_kpi(label: str, nilai: str, sub: str, kritis: bool = False) -> None:
    kelas = "kpi kpi-kritis" if kritis else "kpi"
    st.markdown(
        f'<div class="{kelas}"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{nilai}</div><div class="kpi-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def tampilkan_grafik(fig: go.Figure) -> None:
    st.plotly_chart(fig, config=PLOT_CONFIG, **stretch(st.plotly_chart))


def reset_filter(wilayah: list, komoditas: list, rentang: tuple) -> None:
    """Nielsen #3 - User Control & Freedom: satu klik kembali ke kondisi awal."""
    st.session_state["f_wilayah"] = list(wilayah)
    st.session_state["f_komoditas"] = list(komoditas)
    st.session_state["f_tanggal"] = rentang
    st.session_state.pop("fokus_komoditas", None)


def render_sidebar(df: pd.DataFrame):
    """ZOOM AND FILTER: filter interaktif di sidebar."""
    wilayah_semua = list(WILAYAH.keys())
    komoditas_semua = list(KOMODITAS.keys())
    min_d, max_d = df["tanggal"].min().date(), df["tanggal"].max().date()

    st.session_state.setdefault("f_wilayah", wilayah_semua)
    st.session_state.setdefault("f_komoditas", komoditas_semua)
    st.session_state.setdefault("f_tanggal", (min_d, max_d))
    # Jaga agar state tanggal tetap dalam batas jika dataset bergeser hari
    tgl_state = st.session_state["f_tanggal"]
    if isinstance(tgl_state, (tuple, list)):
        st.session_state["f_tanggal"] = tuple(min(max(t, min_d), max_d) for t in tgl_state)

    with st.sidebar:
        st.header("Filter Data")
        st.caption("Zoom & filter: persempit tampilan sesuai kebutuhan Anda.")
        wilayah = st.multiselect("Wilayah / Pasar", wilayah_semua, key="f_wilayah",
                                 help="Pilih satu atau beberapa kabupaten/kota.")
        komoditas = st.multiselect("Komoditas", komoditas_semua, key="f_komoditas",
                                   help="Pilih satu atau beberapa komoditas pangan.")
        rentang = st.date_input("Rentang tanggal", min_value=min_d, max_value=max_d,
                                key="f_tanggal", format="DD/MM/YYYY",
                                help="Pilih tanggal awal lalu tanggal akhir.")
        st.button("Reset Filter", on_click=reset_filter,
                  args=(wilayah_semua, komoditas_semua, (min_d, max_d)),
                  **stretch(st.button))
        st.divider()
        with st.expander("Panduan singkat"):
            st.markdown(
                "1. Baca **4 kartu ringkasan** di bagian atas.\n"
                "2. Persempit data lewat **filter** di sini.\n"
                "3. Pilih **komoditas fokus** di atas grafik.\n"
                "4. **Arahkan kursor** ke grafik untuk detail & rekomendasi.\n"
                "5. Buka **tabel rincian** bila butuh angka lengkap.\n\n"
                "Warna **merah** = harga > +15% di atas HET."
            )
        st.caption("Data: simulasi untuk keperluan akademik.")
    return wilayah, komoditas, rentang


# =============================================================================
# 7. HALAMAN DASHBOARD
# =============================================================================
def render_dashboard(df: pd.DataFrame, wilayah: list, komoditas: list, rentang) -> None:
    # --- Validasi input (Nielsen #5 Error Prevention & #9 Recover from Errors) ---
    if not isinstance(rentang, (tuple, list)) or len(rentang) != 2:
        st.info("Pilih **tanggal akhir** pada filter rentang tanggal untuk melanjutkan.")
        return
    if not wilayah or not komoditas:
        st.warning("Tidak ada data yang ditampilkan karena filter kosong. "
                   "Pilih minimal satu wilayah dan satu komoditas, atau klik **Reset Filter**.")
        return

    awal, akhir = pd.Timestamp(rentang[0]), pd.Timestamp(rentang[1])
    mask = (df["tanggal"].between(awal, akhir) & df["wilayah"].isin(wilayah) & df["komoditas"].isin(komoditas))
    d = df[mask]
    if d.empty:
        st.warning("Data tidak ditemukan untuk kombinasi filter ini. Klik **Reset Filter** untuk memulai ulang.")
        return

    kpi = hitung_kpi(d, df)

    # --- Status sistem selalu terlihat (Nielsen #1) ---
    st.caption(
        f"Menampilkan **{len(wilayah)} wilayah** · **{len(komoditas)} komoditas** · "
        f"{fmt_tgl(awal)} s.d. {fmt_tgl(akhir)} · data terakhir: **{fmt_tgl(kpi['tgl_akhir'])}**"
    )

    # =========================================================================
    # a) OVERVIEW FIRST - 4 KPI Cards
    # =========================================================================
    st.markdown('<div class="langkah">Langkah 1 · Overview</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi("Komoditas Status Kritis", f"{kpi['n_kom_krit']} dari {kpi['n_kom']}",
                   f"{kpi['n_kombinasi_krit']} kombinasi pasar-komoditas > +{KRITIS_PCT:.0f}% HET",
                   kritis=kpi["n_kom_krit"] > 0)
    with c2:
        render_kpi("Rata-rata Perubahan Harga", fmt_pct(kpi["rata_perubahan"]),
                   "rata-rata 7 hari terakhir vs 7 hari pertama periode",
                   kritis=kpi["rata_perubahan"] > KRITIS_PCT)
    with c3:
        if kpi["n_krit_top"] > 0:
            render_kpi("Wilayah Prioritas Operasi Pasar", kpi["wilayah_top"],
                       f"{kpi['n_krit_top']} komoditas kritis · rata-rata {fmt_pct(kpi['pct_top'])} dari HET",
                       kritis=True)
        else:
            render_kpi("Wilayah Prioritas Operasi Pasar", "Belum ada",
                       "tidak ada wilayah melampaui ambang kritis")
    with c4:
        render_kpi("Status Ketersediaan Stok", kpi["status_stok"],
                   f"stok {fmt_num(kpi['rasio'] * 100)}% dari normal · "
                   f"{kpi['n_tipis']} dari {kpi['n_seri']} seri di bawah {STOK_MENIPIS * 100:.0f}%",
                   kritis=kpi["status_stok"] == "Defisit")

    st.write("")

    # =========================================================================
    # b) ZOOM & FILTER - fokus komoditas untuk grafik detail
    # =========================================================================
    st.markdown('<div class="langkah">Langkah 2 · Zoom &amp; Filter</div>', unsafe_allow_html=True)
    akhir_df = d[d["tanggal"] == kpi["tgl_akhir"]]
    opsi = [k for k in KOMODITAS if k in set(d["komoditas"])]
    terparah = akhir_df.groupby("komoditas")["selisih_pct"].mean().idxmax()
    if st.session_state.get("fokus_komoditas") not in (None, *opsi):
        st.session_state.pop("fokus_komoditas", None)
    fokus = st.selectbox("Komoditas fokus untuk grafik di bawah", opsi,
                         index=opsi.index(terparah), key="fokus_komoditas",
                         help="Default otomatis ke komoditas dengan harga paling jauh di atas HET.")
    satuan = KOMODITAS[fokus]["satuan"]
    d_fokus = d[d["komoditas"] == fokus]
    d_fokus_akhir = d_fokus[d_fokus["tanggal"] == kpi["tgl_akhir"]]
    n_krit_fokus = int((d_fokus_akhir["selisih_pct"] > KRITIS_PCT).sum())
    rata_fokus = float(d_fokus_akhir["selisih_pct"].mean())

    # --- Grafik 1: Line chart tren harian vs HET ---
    st.markdown(f"#### Tren harga {fokus} terhadap HET")
    arah = "di atas" if rata_fokus > 0 else "di bawah"
    st.caption(
        f"Rata-rata harga {fokus} {fmt_pct(abs(rata_fokus)).lstrip('+')} {arah} HET pada "
        f"{fmt_tgl(kpi['tgl_akhir'])}; **{n_krit_fokus} dari {d_fokus_akhir['wilayah'].nunique()} wilayah** "
        f"melampaui ambang kritis. Titik merah = > +{KRITIS_PCT:.0f}% di atas HET. "
        "Arahkan kursor untuk detail."
    )
    tampilkan_grafik(grafik_tren(d_fokus, satuan))

    # --- Grafik 2 & 3 berdampingan (Gestalt: proximity) ---
    kiri, kanan = st.columns(2)
    with kiri:
        st.markdown(f"#### Selisih harga {fokus} antar wilayah")
        st.caption(f"Posisi pada {fmt_tgl(kpi['tgl_akhir'])}, diurutkan dari yang tertinggi.")
        tampilkan_grafik(grafik_selisih(d_fokus_akhir))
    with kanan:
        st.markdown(f"#### Pasokan vs harga {fokus}")
        fig_sc, r = grafik_scatter(d_fokus, satuan)
        st.caption(
            (f"Korelasi stok–harga: {tafsir_korelasi(r)}. " if r is not None else "Data belum cukup untuk korelasi. ")
            + "Korelasi bukan bukti sebab-akibat."
        )
        tampilkan_grafik(fig_sc)

    # =========================================================================
    # c) DETAILS-ON-DEMAND - tabel disembunyikan hingga diminta
    # =========================================================================
    st.markdown('<div class="langkah">Langkah 3 · Details-on-Demand</div>', unsafe_allow_html=True)
    st.caption("Detail presisi tersedia lewat tooltip grafik (hover/klik) dan panel di bawah ini.")
    with st.expander("Rincian komoditas kritis per pasar (data terakhir)"):
        krit_tbl = akhir_df[akhir_df["selisih_pct"] > KRITIS_PCT].sort_values("selisih_pct", ascending=False)
        if krit_tbl.empty:
            st.success("Tidak ada komoditas yang melampaui ambang kritis pada filter ini.")
        else:
            tampil = krit_tbl[["wilayah", "pasar", "komoditas", "harga_fmt", "het_fmt", "selisih_fmt", "tindakan"]]
            tampil.columns = ["Wilayah", "Pasar", "Komoditas", "Harga", "HET", "Selisih HET", "Rekomendasi Tindakan"]
            st.dataframe(tampil, hide_index=True, **stretch(st.dataframe))
    with st.expander("Tabel data lengkap & unduh"):
        lengkap = d[["tanggal", "wilayah", "pasar", "komoditas", "satuan", "harga", "het",
                     "selisih_pct", "stok_ton", "status"]].copy()
        lengkap["tanggal"] = lengkap["tanggal"].dt.strftime("%d/%m/%Y")
        lengkap["selisih_pct"] = lengkap["selisih_pct"].round(1)
        lengkap.columns = ["Tanggal", "Wilayah", "Pasar", "Komoditas", "Satuan", "Harga (Rp)", "HET (Rp)",
                           "Selisih HET (%)", "Stok (ton)", "Status"]
        st.dataframe(lengkap, hide_index=True, **stretch(st.dataframe))
        st.download_button("Unduh data terfilter (CSV)", lengkap.to_csv(index=False).encode("utf-8"),
                           file_name="harga_pangan_bengkulu_terfilter.csv", mime="text/csv")


# =============================================================================
# 8. TAB DOKUMENTASI PRINSIP HCI & USER PERSONA
# =============================================================================
def render_dokumentasi() -> None:
    st.header("Dokumentasi Prinsip HCI & User Persona")
    st.caption("Referensi teori: materi kuliah praktisi Dr. Arafat Febriandirza (BRIN). "
               "Persona bersifat fiktif dan disusun untuk keperluan akademik.")

    # ------------------------------------------------------------------ Persona
    st.subheader("1. User Persona: Ibu Ratna")
    with st.container(border=True):
        kol_a, kol_b = st.columns([1, 2])
        with kol_a:
            st.markdown(
                "**Ibu Ratna Kusumawati, S.P., M.Si.**  \n"
                "*Kepala Bidang Distribusi Pangan*  \n"
                "Dinas Ketahanan Pangan Provinsi Bengkulu\n\n"
                "**Demografi**\n"
                "- Usia 47 tahun, S2 Agribisnis\n"
                "- 21 tahun sebagai ASN, berkantor di Kota Bengkulu\n"
                "- Literasi digital menengah: nyaman dengan WhatsApp, e-mail, dan Excel dasar\n"
                "- Perangkat: laptop kantor (utama) dan smartphone Android"
            )
        with kol_b:
            st.markdown(
                "**Goals**\n"
                "- Mengetahui dalam < 5 menit komoditas dan wilayah mana yang melampaui HET\n"
                "- Menentukan prioritas lokasi operasi pasar secara cepat dan berbasis data\n"
                "- Menyiapkan bahan paparan ringkas untuk rapat koordinasi pengendalian inflasi daerah\n"
                "- Mendeteksi dini potensi kenaikan inflasi sebelum rilis resmi bulanan\n\n"
                "**Pain Points**\n"
                "- Data tersebar di banyak spreadsheet dan laporan WhatsApp petugas pasar\n"
                "- Grafik yang padat membuatnya sulit menemukan masalah utama\n"
                "- Tidak ada penanda otomatis untuk harga yang melewati batas\n"
                "- Waktu terbatas dan takut salah membaca angka di depan pimpinan\n\n"
                "**Behavior**\n"
                "- Membuka laporan pagi hari sebelum rapat\n"
                "- Menyukai tampilan ringkas, angka besar, dan penanda warna\n"
                "- Sering mengirim tangkapan layar ke grup koordinasi\n"
                "- Mendelegasikan analisis mendalam ke staf"
            )

    st.markdown("**Skenario penggunaan**")
    st.markdown(
        "| Unsur | Uraian |\n|---|---|\n"
        "| **Context** | Senin pagi, 30 menit sebelum rapat koordinasi pengendalian inflasi daerah; membuka dashboard di laptop kantor. |\n"
        "| **Trigger** | Kepala Dinas mengirim pesan WhatsApp tentang keluhan kenaikan harga cabai di pasar. |\n"
        "| **Action** | Membaca 4 KPI, melihat wilayah prioritas, memilih fokus Cabai Merah, mengamati titik merah, hover untuk rekomendasi, membuka tabel rincian. |\n"
        "| **Outcome** | Dalam < 5 menit memutuskan operasi pasar di wilayah prioritas dan memperoleh bahan paparan yang siap dipakai. |"
    )

    # ------------------------------------------------------------------ Prinsip
    st.subheader("2. Prinsip kognitif & visualisasi yang diterapkan")

    with st.expander("Cognitive Load Theory"):
        st.markdown(
            "- **Intrinsic load** (kompleksitas data: 6 komoditas x 5 wilayah x 90 hari) dikelola dengan *chunking*: "
            "empat KPI Card di awal dan satu komoditas fokus untuk grafik detail.\n"
            "- **Extraneous load** ditekan: tanpa grid berlebihan, tanpa legenda terpisah (label langsung), "
            "detail angka disembunyikan di tooltip dan expander, hanya satu warna alarm.\n"
            "- **Germane load** didukung oleh urutan baca yang konsisten (Overview, Zoom & Filter, Details), "
            "kalimat ringkasan di atas grafik, dan kode warna yang sama di seluruh halaman."
        )
    with st.expander("Preattentive Attributes"):
        st.markdown(
            "- **Hue/warna:** biru-abu lembut untuk data normal; **merah menyala** otomatis hanya untuk data > +15% di atas HET, "
            "sehingga mata menemukannya dalam hitungan milidetik tanpa membaca angka.\n"
            "- **Panjang & posisi:** horizontal bar diurutkan dari nilai tertinggi.\n"
            "- **Ukuran:** titik kritis sedikit lebih besar dan lebih pekat daripada titik normal.\n"
            "- **Orientasi/pola garis:** garis putus-putus sebagai batas acuan (HET) dan ambang kritis."
        )
    with st.expander("Psikologi Gestalt"):
        st.markdown(
            "- **Proximity:** empat KPI Card berdekatan sebagai satu kelompok; bar dan scatter berdampingan.\n"
            "- **Similarity:** warna yang sama berarti kategori yang sama (biru = normal, merah = kritis) di semua grafik.\n"
            "- **Figure-ground:** garis wilayah abu-abu menjadi latar, rata-rata biru tebal dan titik merah menjadi figur.\n"
            "- **Continuity:** line chart dan garis HET horizontal memandu mata mengikuti tren.\n"
            "- **Closure:** grafik tanpa kotak/bingkai; otak melengkapi batas area plot.\n"
            "- **Common region:** kartu KPI dan kartu persona memakai border untuk mengelompokkan isi."
        )
    with st.expander("Edward Tufte: Data-Ink Ratio & Anti-Chartjunk"):
        st.markdown(
            "- Template `simple_white`: grid, latar, dan border dihapus; tinta dipakai untuk data.\n"
            "- Tanpa efek 3D, gradien, atau dekorasi; tidak ada legenda yang memaksa mata bolak-balik.\n"
            "- Label langsung pada garis acuan dan nilai langsung di ujung bar.\n"
            "- Bar chart memakai garis nol = HET sehingga proporsi visual jujur (menghindari *lie factor*).\n"
            "- Pemilihan grafik: **line** untuk tren waktu, **horizontal bar** untuk perbandingan antar kategori, "
            "**scatter** untuk hubungan dua variabel numerik."
        )
    with st.expander("Shneiderman's Visual Information Seeking Mantra"):
        st.markdown(
            "- **Overview first:** 4 KPI Card di bagian paling atas.\n"
            "- **Zoom and filter:** sidebar (wilayah, komoditas, rentang tanggal) dan komoditas fokus.\n"
            "- **Details-on-demand:** tooltip hover berisi harga presisi, selisih HET, stok, dan rekomendasi tindakan; "
            "tabel rincian dan unduhan CSV berada di dalam expander."
        )
    with st.expander("10 Heuristik Usability Jakob Nielsen"):
        st.markdown(
            "| # | Heuristik | Implementasi pada dashboard |\n|---|---|---|\n"
            "| 1 | Visibility of system status | Baris status filter aktif dan tanggal data terakhir; KPI status stok (Aman/Menipis/Defisit). |\n"
            "| 2 | Match between system & real world | Bahasa Indonesia, istilah dinas (HET, operasi pasar), format Rp dan angka Indonesia. |\n"
            "| 3 | User control & freedom | Tombol **Reset Filter**; filter dapat diubah kapan saja; expander dapat ditutup. |\n"
            "| 4 | Consistency & standards | Kartu KPI seragam; merah selalu berarti kritis; jenis grafik sesuai konvensi. |\n"
            "| 5 | Error prevention | Rentang tanggal dibatasi; filter kosong dan tanggal belum lengkap ditangani. |\n"
            "| 6 | Recognition rather than recall | Label langsung pada grafik, semua opsi filter terlihat, tooltip bantuan. |\n"
            "| 7 | Flexibility & efficiency of use | Komoditas fokus default ke yang paling kritis; pengguna mahir dapat memfilter bebas dan mengunduh CSV. |\n"
            "| 8 | Aesthetic & minimalist design | Data-ink ratio tinggi, detail disembunyikan sampai diminta. |\n"
            "| 9 | Help users recover from errors | Pesan peringatan jelas disertai solusi (pilih minimal satu opsi atau Reset Filter). |\n"
            "| 10 | Help & documentation | Panduan singkat di sidebar dan tab dokumentasi ini. |"
        )

    st.subheader("3. Catatan metodologi")
    st.markdown(
        f"- Ambang kritis = harga **> {KRITIS_PCT:.0f}%** di atas HET; waspada = > {WASPADA_PCT:.0f}%.\n"
        "- Seluruh data adalah **simulasi**; nilai HET bersifat ilustratif dan perlu disesuaikan dengan regulasi terbaru "
        "bila dipakai pada data nyata.\n"
        "- Dataset dibangkitkan dengan seed tetap sehingga hasilnya dapat direproduksi."
    )


# =============================================================================
# 9. MAIN
# =============================================================================
def main() -> None:
    st.set_page_config(page_title="Dashboard Pangan Bengkulu", page_icon="📊", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)

    df = generate_dataset(anchor=date.today().isoformat())
    wilayah, komoditas, rentang = render_sidebar(df)

    st.title("Dashboard Eksekutif Pemantauan Harga Pangan")
    st.markdown("Deteksi dini inflasi daerah · **Dinas Ketahanan Pangan Provinsi Bengkulu**")

    tab_dashboard, tab_dokumentasi = st.tabs(["Dashboard Eksekutif", "Dokumentasi Prinsip HCI & User Persona"])
    with tab_dashboard:
        render_dashboard(df, wilayah, komoditas, rentang)
    with tab_dokumentasi:
        render_dokumentasi()


if __name__ == "__main__":
    main()
