import calendar
import os
import io
import base64
from datetime import datetime, time, date, timedelta
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

def get_internal_daily_counts(db, target_date: date, mode: str = "working", cam_id: str = None):
    start_wib = datetime.combine(target_date, time.min, tzinfo=WIB)
    end_wib = datetime.combine(target_date, time.max, tzinfo=WIB)
    start_utc = start_wib.astimezone(UTC)
    end_utc = end_wib.astimezone(UTC)

    query = db.query(Screenshot.event_type, func.count(Screenshot.id).label("total"))\
              .filter(Screenshot.timestamp >= start_utc, Screenshot.timestamp < end_utc)

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

def get_monthly_matrix_data(year: int, month: int, mode: str = "working"):
    violation_keys = ["no_hardhat", "no_mask", "no_glove", "no_shoes", "short_sleeve"]
    _, days_in_month = calendar.monthrange(year, month)
    
    daily_data = []
    row_totals = {key: 0 for key in violation_keys}
    grand_total = 0

    db = SessionLocal()
    try:
        for day in range(1, days_in_month + 1):
            target_date = date(year, month, day)
            raw_counts = get_internal_daily_counts(db, target_date, mode)
            
            daily_total = sum(raw_counts.values())
            daily_data.append({
                "dateLabel": f"{day:02d}",
                "counts": raw_counts,
                "dailyTotal": daily_total
            })

            for key in violation_keys:
                row_totals[key] += raw_counts.get(key, 0)
            grand_total += daily_total
    finally:
        db.close()

    return {"daily_data": daily_data, "violation_keys": violation_keys, "row_totals": row_totals, "grand_total": grand_total}

def generate_chart_base64(daily_data, violation_keys, label_map):
    """Membuat grafik Matplotlib  / Chart.js dan Rata Kiri-Kanan"""
    colors = ['#ef4444', '#f97316', '#a855f7', '#3b82f6', '#10b981']
    
    # figsize diperlebar agar resolusi aman saat ditarik 100% di PDF
    fig = Figure(figsize=(13, 3)) 
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    
    days = [d['dateLabel'] for d in daily_data]
    max_y = 0
    
    for i, key in enumerate(violation_keys):
        counts = [d['counts'].get(key, 0) for d in daily_data]
        if counts:
            max_y = max(max_y, max(counts))
        ax.plot(days, counts, color=colors[i % len(colors)], linewidth=1.8, marker='o', markersize=3.5, zorder=3)

    # Atur Interval Y-Axis persis seperti Chart.js
    ax.set_ylim(bottom=0)
    if max_y > 0:
        ax.set_ylim(top=(int(max_y / 100) + 1) * 100)

    # Hilangkan bingkai kaku Matplotlib (Spines)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#cccccc')

    # Buat Grid Garis Lurus tipis warna abu-abu
    ax.grid(True, axis='both', color='#e5e5e5', linestyle='-', linewidth=0.8, zorder=0)
    ax.tick_params(axis='both', which='major', labelsize=8, colors='#666666', length=0)
    
    # Legend Custom: Ubah garis menjadi KOTAK ala Chart.js
    custom_handles = [Line2D([0], [0], color=colors[i], lw=0, marker='s', markersize=6) for i in range(len(violation_keys))]
    legend_labels = [label_map[k] for k in violation_keys]
    
    ax.legend(custom_handles, legend_labels, loc='lower center', 
              bbox_to_anchor=(0.5, -0.35), ncol=5, fontsize=8, 
              frameon=False, handletextpad=0.5)
    
    # PANGKAS MARGIN: Agar grafik menyentuh ujung kiri dan kanan
    ax.margins(x=0)
    fig.subplots_adjust(bottom=0.25, top=0.92, left=0.015, right=0.985)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, transparent=True)
    buf.seek(0)
    b64_string = base64.b64encode(buf.read()).decode('utf-8')
    return b64_string

def generate_apd_pdf(year: int, month: int, mode: str = "working"):
    print("   -> [GENERATOR] Query data harian dari database...", flush=True)
    data = get_monthly_matrix_data(year, month, mode)
    
    label_map = {
        "no_hardhat": "No Helmet", "no_mask": "No Mask", 
        "no_glove": "No Glove", "no_shoes": "No Shoes", "short_sleeve": "Short Sleeve"
    }
    
    months_id = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    month_label = months_id[month]
    today_label = datetime.now(WIB).strftime("%d %B %Y")

    print("   -> [GENERATOR] Membangun grafik Matplotlib ke Base64...", flush=True)
    chart_b64 = generate_chart_base64(data["daily_data"], data["violation_keys"], label_map)

    current_dir = os.path.dirname(__file__)
    design_dir = os.path.join(current_dir, '../design')
    
    print("   -> [GENERATOR] Merender template HTML (Jinja2)...", flush=True)
    env = Environment(loader=FileSystemLoader(design_dir))
    template = env.get_template('report_monthly.html')
    
    html_out = template.render(
        current_year=year, month_label=month_label, today_label=today_label,
        daily_data=data["daily_data"], violation_keys=data["violation_keys"],
        label_map=label_map, row_totals=data["row_totals"], grand_total=data["grand_total"],
        chart_base64=chart_b64
    )

    root_dir = os.path.abspath(os.path.join(current_dir, '../../../../'))
    temp_dir = os.path.join(root_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    pdf_path = os.path.join(temp_dir, f"Laporan_APD_{month_label}_{year}.pdf")
    
    print("   -> [GENERATOR] Memulai WeasyPrint untuk konversi HTML ke PDF...", flush=True)
    HTML(string=html_out, base_url=design_dir).write_pdf(pdf_path)
    
    print("   -> [GENERATOR] Konversi PDF selesai!", flush=True)
    return pdf_path