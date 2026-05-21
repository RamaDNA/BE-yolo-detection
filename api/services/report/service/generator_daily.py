import os
import io
import base64
from datetime import datetime, time, date
from zoneinfo import ZoneInfo
from sqlalchemy import func, or_, and_

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.lines import Line2D

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from db.db import SessionLocal
from db.models import Screenshot

WIB = ZoneInfo("Asia/Jakarta")
UTC = ZoneInfo("UTC")

BREAK_TIMES = [
    ("06:54", "07:15"), ("11:00", "13:00"), 
    ("15:00", "15:30"), ("17:30", "18:30"), ("22:45", "23:15")
]

def build_break_ranges_wib(date_filter: date):
    ranges = []
    for start_str, end_str in BREAK_TIMES:
        start = datetime.combine(date_filter, datetime.strptime(start_str, "%H:%M").time(), tzinfo=WIB)
        end = datetime.combine(date_filter, datetime.strptime(end_str, "%H:%M").time(), tzinfo=WIB)
        ranges.append((start.astimezone(UTC), end.astimezone(UTC)))
    return ranges

def get_internal_hourly_counts(db, target_date: date, hour: int, mode: str = "working", cam_id: str = None):
    """Mengambil jumlah pelanggaran dalam rentang 1 jam (WIB dikonversi ke UTC untuk query)"""
    start_wib = datetime.combine(target_date, time(hour=hour, minute=0, second=0), tzinfo=WIB)
    end_wib = datetime.combine(target_date, time(hour=hour, minute=59, second=59), tzinfo=WIB)
    
    start_utc = start_wib.astimezone(UTC)
    end_utc = end_wib.astimezone(UTC)

    query = db.query(Screenshot.event_type, func.count(Screenshot.id).label("total"))\
              .filter(Screenshot.timestamp >= start_utc, Screenshot.timestamp <= end_utc)

    if cam_id:
        query = query.filter(Screenshot.cam_id == cam_id)

    if mode != "all":
        break_ranges = build_break_ranges_wib(target_date)
        if mode == "break":
            conditions = [and_(Screenshot.timestamp >= s, Screenshot.timestamp <= e) for s, e in break_ranges]
            if conditions:
                query = query.filter(or_(*conditions))
        elif mode == "working":
            for s, e in break_ranges:
                query = query.filter(~and_(Screenshot.timestamp >= s, Screenshot.timestamp <= e))

    stats = query.group_by(Screenshot.event_type).all()
    return {row[0] if row[0] else "unknown": row[1] for row in stats}

def get_daily_matrix_data(target_date: date, mode: str = "working"):
    """Menghasilkan array 24 jam (00:00 - 23:00)"""
    violation_keys = ["no_hardhat", "no_mask", "no_glove", "no_shoes", "short_sleeve"]
    hourly_data = []
    row_totals = {key: 0 for key in violation_keys}
    grand_total = 0

    db = SessionLocal()
    try:
        # Looping 24 jam untuk 24 kolom di PDF Landscape
        for hour in range(24):
            raw_counts = get_internal_hourly_counts(db, target_date, hour, mode)
            
            hourly_total = sum(raw_counts.values())
            hourly_data.append({
                "hourLabel": f"{hour:02d}:00",
                "counts": raw_counts,
                "total": hourly_total
            })

            # Akumulasi total per baris (jenis pelanggaran)
            for key in violation_keys:
                row_totals[key] += raw_counts.get(key, 0)
            grand_total += hourly_total
    finally:
        db.close()

    return {
        "hourly_data": hourly_data, 
        "violation_keys": violation_keys, 
        "row_totals": row_totals, 
        "grand_total": grand_total
    }

def generate_daily_chart_base64(hourly_data, violation_keys, label_map):
    """Membuat grafik Line Chart per jam bergaya Chart.js"""
    colors = ['#ef4444', '#f97316', '#a855f7', '#3b82f6', '#10b981']
    
    # figsize=13,3 menyesuaikan lebar kertas A4 Landscape
    fig = Figure(figsize=(13, 3)) 
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    
    hours = [d['hourLabel'] for d in hourly_data]
    max_y = 0
    
    for i, key in enumerate(violation_keys):
        counts = [d['counts'].get(key, 0) for d in hourly_data]
        if counts:
            max_y = max(max_y, max(counts))
        ax.plot(hours, counts, color=colors[i % len(colors)], linewidth=1.8, marker='o', markersize=3.5, zorder=3)

    ax.set_ylim(bottom=0)
    if max_y > 0:
        if max_y < 10:
            ax.set_ylim(top=10)
        else:
            ax.set_ylim(top=(int(max_y / 50) + 1) * 50)

    # Styling identik dengan versi bulanan
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#cccccc')

    ax.grid(True, axis='both', color='#e5e5e5', linestyle='-', linewidth=0.8, zorder=0)
    
    # Font jam dikecilkan sedikit agar 24 titik tidak bertabrakan
    ax.tick_params(axis='both', which='major', labelsize=6.5, colors='#666666', length=0)
    
    custom_handles = [Line2D([0], [0], color=colors[i], lw=0, marker='s', markersize=6) for i in range(len(violation_keys))]
    legend_labels = [label_map[k] for k in violation_keys]
    
    ax.legend(custom_handles, legend_labels, loc='lower center', 
              bbox_to_anchor=(0.5, -0.35), ncol=5, fontsize=8, 
              frameon=False, handletextpad=0.5)
    
    ax.margins(x=0)
    fig.subplots_adjust(bottom=0.25, top=0.92, left=0.015, right=0.985)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, transparent=True)
    buf.seek(0)
    b64_string = base64.b64encode(buf.read()).decode('utf-8')
    return b64_string

def generate_apd_daily_pdf(target_date: date, mode: str = "working"):
    """Fungsi eksekusi utama untuk PDF Harian"""
    print(f"   -> [GENERATOR DAILY] Query data harian untuk tanggal {target_date}...", flush=True)
    data = get_daily_matrix_data(target_date, mode)
    
    label_map = {
        "no_hardhat": "No Helmet", "no_mask": "No Mask", 
        "no_glove": "No Glove", "no_shoes": "No Shoes", "short_sleeve": "Short Sleeve"
    }
    
    months_id = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    target_date_label = f"{target_date.day:02d} {months_id[target_date.month]} {target_date.year}"
    today_label = datetime.now(WIB).strftime("%d %B %Y")

    print("   -> [GENERATOR DAILY] Membangun grafik Matplotlib Harian...", flush=True)
    chart_b64 = generate_daily_chart_base64(data["hourly_data"], data["violation_keys"], label_map)

    current_dir = os.path.dirname(__file__)
    design_dir = os.path.join(current_dir, '../design')
    
    print("   -> [GENERATOR DAILY] Merender template HTML Harian...", flush=True)
    env = Environment(loader=FileSystemLoader(design_dir))
    template = env.get_template('report_daily.html')
    
    html_out = template.render(
        target_date_label=target_date_label, 
        today_label=today_label,
        hourly_data=data["hourly_data"], 
        violation_keys=data["violation_keys"],
        label_map=label_map, 
        row_totals=data["row_totals"], 
        grand_total=data["grand_total"],
        chart_base64=chart_b64
    )

    root_dir = os.path.abspath(os.path.join(current_dir, '../../../../'))
    temp_dir = os.path.join(root_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    pdf_path = os.path.join(temp_dir, f"Laporan_APD_Harian_{target_date.strftime('%Y%m%d')}.pdf")
    
    print("   -> [GENERATOR DAILY] Memulai WeasyPrint...", flush=True)
    HTML(string=html_out, base_url=design_dir).write_pdf(pdf_path)
    
    print("   -> [GENERATOR DAILY] Konversi PDF Harian selesai!", flush=True)
    return pdf_path