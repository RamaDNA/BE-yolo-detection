import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email_with_attachment(subject, body, to_email, from_email, password, attachment_path):
    print(f">>> [SMTP] Memulai proses pengiriman ke {to_email}...", flush=True)
    
    if not os.path.exists(attachment_path):
        print(f">>> [SMTP ERROR] File tidak ada: {attachment_path}", flush=True)
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with open(attachment_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(attachment_path)}")
            msg.attach(part)

        # --- PERBAIKAN KRUSIAL DI SINI ---
        print(">>> [SMTP] Mendapatkan IP Gmail via IPv4...", flush=True)
        # Memaksa resolusi DNS ke IPv4 agar tidak terjebak di IPv6 Docker
        gmail_ipv4 = socket.gethostbyname('smtp.gmail.com')
        
        print(f">>> [SMTP] Menghubungi {gmail_ipv4} via Port 465 (SSL)...", flush=True)
        # Port 465 (SMTP_SSL) jauh lebih stabil di lingkungan Docker/Server
        server = smtplib.SMTP_SSL(gmail_ipv4, 465, timeout=30)
        
        # Aktifkan ini jika ingin melihat log komunikasi detail di terminal
        # server.set_debuglevel(1) 

        print(">>> [SMTP] Mencoba login...", flush=True)
        server.login(from_email, password)
        
        print(">>> [SMTP] Mengirim data...", flush=True)
        server.send_message(msg)
        
        server.quit()
        print(">>> [SMTP] Email berhasil terkirim!", flush=True)
        return True

    except socket.timeout:
        print(">>> [SMTP ERROR] Koneksi timeout! Cek firewall atau MTU Docker.", flush=True)
    except smtplib.SMTPAuthenticationError:
        print(">>> [SMTP ERROR] Gagal login! Cek App Password Gmail Anda.", flush=True)
    except Exception as e:
        print(f">>> [SMTP ERROR] Error: {e}", flush=True)
    return False