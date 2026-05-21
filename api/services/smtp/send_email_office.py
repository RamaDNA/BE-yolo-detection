import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import socket

# =====================================================================
# PATCH: force SMTP library to use IPv4 (bypass IPv6) 
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo
# =====================================================================

def send_email_with_attachment(subject, body, to_email, from_email, password, attachment_path):
    print(f">>> [SMTP] Memulai proses pengiriman ke {to_email}...", flush=True)
    
    # 1. Validation File
    if not os.path.exists(attachment_path):
        print(f">>> [SMTP ERROR] File attachment tidak ditemukan: {attachment_path}", flush=True)
        return False
        
    try:
        # 2. setup MIME
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # 3. process attachment
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(attachment_path)}")
            msg.attach(part)

        # 4. init SMTP Connection (Office 365)
        print(">>> [SMTP] Menyiapkan instance SMTP (Force IPv4)...", flush=True)
        server = smtplib.SMTP(timeout=30)
        
        # debug level
        server.set_debuglevel(1) 

        print(">>> [SMTP] Menghubungi smtp.office365.com via Port 587...", flush=True)
        server.connect('smtp.office365.com', 587)

        # 5. Protokol Keamanan & Login
        server.ehlo() 
        
        server._host = "smtp.office365.com"
        
        print(">>> [SMTP] Mengaktifkan enkripsi STARTTLS...", flush=True)
        server.starttls() 
        
        server.ehlo() 

        print(">>> [SMTP] Mencoba login otentikasi...", flush=True)
        server.login(from_email, password)
        
        # 6. send email
        print(">>> [SMTP] Mengirim paket data email...", flush=True)
        server.send_message(msg)
        
        # 7. quit connection
        server.quit()
        print(">>> [SMTP] Laporan APD berhasil terkirim ke Office 365!", flush=True)
        return True

    except smtplib.SMTPConnectError:
        print(">>> [SMTP ERROR] Gagal terhubung ke server.", flush=True)
    except TimeoutError:
        print(">>> [SMTP ERROR] Koneksi timeout!", flush=True)
    except smtplib.SMTPAuthenticationError:
        print(">>> [SMTP ERROR] Gagal login! Pastikan Authenticated SMTP aktif dan App Password benar.", flush=True)
    except Exception as e:
        print(f">>> [SMTP ERROR] Error tidak terduga: {e}", flush=True)
        
    return False