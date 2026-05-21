from apscheduler.schedulers.background import BackgroundScheduler
from services.smtp.send_email_office import send_email_with_attachment
from services.report.service.generator_daily import generate_apd_daily_pdf 

# module what'sapp (Path Baru Disesuaikan)
from services.whatsapp.send_whatsapp import send_wa_with_attachment 

from datetime import datetime
import os
from zoneinfo import ZoneInfo
import logging 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('apscheduler')

WIB = ZoneInfo("Asia/Jakarta")
scheduler_daily = BackgroundScheduler(timezone=WIB)

def job_laporan_harian():
    print("--- FUNCTION JOB HARIAN EXECUTE ---", flush=True) 
    
    # ---------------------------------------------------------
    # GENERATE PDF HARIAN
    # ---------------------------------------------------------
    try:
        now = datetime.now(WIB)
        target_date = now.date() 

        print(f"[{now}] Menyiapkan laporan APD harian tanggal {target_date}...", flush=True)
        pdf_path = generate_apd_daily_pdf(target_date)
        
    except Exception as e:
        print(f">>> [FATAL ERROR] Gagal membuat PDF harian. Proses dihentikan: {e}", flush=True)
        return 

    # ---------------------------------------------------------
    # SEND EMAIL HARIAN (Office 365)
    # ---------------------------------------------------------
    try:
        print(">>> Memulai pengiriman Email Harian...", flush=True)

        success_email = send_email_with_attachment(
            subject=f"AUTO-REPORT: Pelanggaran APD Harian - {target_date}",
            body=f"Halo Bapak/Ibu,\n\nTerlampir laporan HARIAN kepatuhan APD otomatis hasil deteksi AI VISION PROTOTYPE ON JEMBO untuk tanggal {target_date}.\n\nSalam,\nHSE Automation System",
            to_email=os.getenv("REPORT_RECIPIENT_1"),  # <-- Disesuaikan Dinamis
            from_email="pklit@jembo.com",   
            password=os.getenv("SMTP_PASSWORD_OFFICE"),  
            attachment_path=pdf_path
        )
        if success_email:
            print(f" success: Report Harian {target_date} already send via email.", flush=True)
            
    except Exception as e:
        print(f"Error while sending daily email: {e}", flush=True)

    # ---------------------------------------------------------
    # SEND WHATSAPP HARIAN (GoWA)
    # ---------------------------------------------------------
    try:
        print(">>> Memulai pengiriman WhatsApp Harian...", flush=True)
        
        wa_target_number = os.getenv("WA_TARGET_NUMBER")
        
        if not wa_target_number:
            print(">>> [ERROR WA] WA_TARGET_NUMBER tidak ditemukan di file .env!", flush=True)
        else:
            wa_caption = f"Laporan Harian Pelanggaran APD (AI Vision PT Jembo)\nTanggal: {target_date}\n\nSilakan unduh dokumen terlampir."
            
            success_wa = send_wa_with_attachment(
                phone_number=wa_target_number,
                caption=wa_caption,
                file_path=pdf_path
            )
            if success_wa:
                print(f" success: Report Harian {target_date} already send via WA.", flush=True)
    except Exception as e:
        print(f">>> [ERROR WA] Pengiriman WhatsApp gagal: {e}", flush=True)

    print("--- FUNCTION JOB HARIAN SELESAI ---", flush=True)


def start_daily_scheduler():
    # Silakan ubah jam ini sesuai kebutuhan kapan laporan harian mau dikirim
    # Misal: Kirim laporan harian setiap jam 23:50 malam
    scheduler_daily.add_job(job_laporan_harian, 'cron', hour=23, minute=59) 
    
    # Untuk testing per beberapa menit:
    # scheduler_daily.add_job(job_laporan_harian, 'cron', minute='*/5')
    
    scheduler_daily.start()
    print("Daily Scheduler Start", flush=True)