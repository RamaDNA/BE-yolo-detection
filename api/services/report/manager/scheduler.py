from apscheduler.schedulers.background import BackgroundScheduler
from services.smtp.send_email import send_email_with_attachment
from services.report.service.generator import generate_apd_pdf
from datetime import datetime, timedelta
import os
from zoneinfo import ZoneInfo
import logging 

# Aktifkan log bawaan Python (wajib di Docker agar error scheduler kelihatan)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('apscheduler')

WIB = ZoneInfo("Asia/Jakarta")
scheduler = BackgroundScheduler(timezone=WIB)

def job_laporan_bulanan():
    print("--- FUNCTION JOB EXECUTE ---", flush=True) 
    
    try:
        now = datetime.now(WIB) 
        last_month_date = now.replace(day=1) - timedelta(days=1)
        target_month = last_month_date.month
        target_year = last_month_date.year

        print(f"[{now}] Menyiapkan laporan APD bulan {target_month}/{target_year}...", flush=True)
        
        pdf_path = generate_apd_pdf(target_year, target_month)
        
        success = send_email_with_attachment(
            subject=f"AUTO-REPORT: Pelanggaran APD - Bulan {target_month}/{target_year}",
            body="Halo Bapak/Ibu,\n\nTerlampir laporan bulanan APD otomatis hasil deteksi AI Vision.\n\nSalam,\nSistem AI Vision PT Jembo",
            to_email="jiwamantap888@gmail.com",
            from_email="fairuzbachri10@gmail.com",
            password=os.getenv("SMTP_PASSWORD"),
            attachment_path=pdf_path
        )
        if success:
            print(f" success: Report {target_month}/{target_year} already send email.", flush=True)
            
    except Exception as e:
        print(f"Error while create otomation email: {e}", flush=True)

def start_report_scheduler():
    scheduler.add_job(job_laporan_bulanan, 'cron', day=7, hour=14, minute=54) 
    
    scheduler.start()
    print("Scheduler Start", flush=True)