from apscheduler.schedulers.background import BackgroundScheduler
from services.smtp.send_email_office import send_email_with_attachment
from services.report.service.generator import generate_apd_pdf

# module what'sapp
from services.whatsapp.send_whatsapp import send_wa_with_attachment 

from datetime import datetime, timedelta
import os
from zoneinfo import ZoneInfo
import logging 

# log activation docker
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('apscheduler')

WIB = ZoneInfo("Asia/Jakarta")
scheduler = BackgroundScheduler(timezone=WIB)

def job_laporan_bulanan():
    print("--- FUNCTION JOB EXECUTE ---", flush=True) 
    
    # ---------------------------------------------------------
    # GENERATE PDF
    # ---------------------------------------------------------
    try:
        now = datetime.now(WIB) 
        last_month_date = now.replace(day=1) - timedelta(days=1)
        target_month = last_month_date.month
        target_year = last_month_date.year

        print(f"[{now}] Menyiapkan laporan APD bulan {target_month}/{target_year}...", flush=True)
        
        pdf_path = generate_apd_pdf(target_year, target_month)
        
    except Exception as e:
        print(f">>> [FATAL ERROR] Gagal membuat PDF laporan. Proses dihentikan: {e}", flush=True)
        return 

    # ---------------------------------------------------------
    # SEND EMAIL (Office 365)
    # ---------------------------------------------------------
    try:
        print(">>> Memulai pengiriman Email...", flush=True)
        
        sender_email = os.getenv("SMTP_USER")
        email_1 = os.getenv("REPORT_RECIPIENT_1")
        email_2 = os.getenv("REPORT_RECIPIENT_2")
        email_3 = os.getenv("REPORT_RECIPIENT_3")

        # Masukkan ke dalam list (dan filter jika ada yang kosong/None)
        list_penerima = [email for email in [email_1, email_2, email_3] if email]

        success_email = send_email_with_attachment(
            subject=f"AUTO-REPORT: Pelanggaran APD - Bulan {target_month}/{target_year}",
            body="Halo Bapak/Ibu,\n\nTerlampir laporan bulanan APD otomatis hasil deteksi AI VISION PROTOTYPE ON JEMBO.\n\nSalam,\nHSE Automation System",
            to_email=list_penerima,  # <-- Berubah (Bisa kirim ke banyak penerima sekaligus)
            from_email="pklit@jembo.com",   # <-- Berubah (WAJIB SAMA dengan yang login di SMTP Office 365)
            password=os.getenv("SMTP_PASSWORD_OFFICE"),  # <-- Berubah
            attachment_path=pdf_path
        )
        if success_email:
            print(f" success: Report {target_month}/{target_year} already send email.", flush=True)
            
    except Exception as e:
        print(f"Error while create otomation email: {e}", flush=True)

    # ---------------------------------------------------------
    # SEND WHATSAPP (GoWA)
    # ---------------------------------------------------------
    try:
        print(">>> Memulai pengiriman WhatsApp...", flush=True)
        
        
        wa_target_number = os.getenv("WA_GROUP_MASSAGE")
        
        if not wa_target_number:
            print(">>> [ERROR WA] WA_TARGET_NUMBER tidak ditemukan di file .env!", flush=True)
        else:
            wa_caption = f"Laporan Bulanan Pelanggaran APD (AI Vision PT Jembo)\nPeriode: {target_month}/{target_year}\n\nSilakan unduh dokumen terlampir."
            
            success_wa = send_wa_with_attachment(
                phone_number=wa_target_number,
                caption=wa_caption,
                file_path=pdf_path
            )
    except Exception as e:
        print(f">>> [ERROR WA] Pengiriman WhatsApp gagal: {e}", flush=True)

    print("--- FUNCTION JOB SELESAI ---", flush=True)


def start_report_scheduler():
    scheduler.add_job(job_laporan_bulanan, 'cron', day=1, hour=8, minute=0) 
    
    scheduler.start()
    print("Scheduler Start", flush=True)