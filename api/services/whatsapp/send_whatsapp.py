import requests
import os

def send_wa_with_attachment(phone_number, caption, file_path):
    print(f">>> [WA] Memulai persiapan pengiriman WA ke {phone_number}...", flush=True)
    
    if not os.path.exists(file_path):
        print(f">>> [WA ERROR] File PDF tidak ditemukan di: {file_path}", flush=True)
        return False

    url = os.getenv("WA_API_URL")
    device_id = os.getenv("wa_device_id_01")
    
    if not url or not device_id:
        print(">>> [WA ERROR] WA_API_URL atau WA_DEVICE_ID belum di-setting di file .env!", flush=True)
        return False

    headers = {
        "X-Device-Id": device_id
    }

    if not phone_number.endswith('@g.us') and not phone_number.endswith('@g.us'):
        phone_number = f"{phone_number}@g.us"

    data = {
        "phone": phone_number,
        "caption": caption,
        "is_forwarded": "false" 
    }

    try:
        print(f">>> [WA] Menghubungi server GoWA ({url})...", flush=True)
        with open(file_path, 'rb') as f:
            files = {
                'file': (os.path.basename(file_path), f, 'application/pdf')
            }
            response = requests.post(url, headers=headers, data=data, files=files, timeout=30)

        if response.status_code == 200:
            print(">>> [WA] SUKSES! Laporan PDF berhasil dikirim ke WhatsApp.", flush=True)
            return True
        else:
            print(f">>> [WA ERROR] Gagal mengirim pesan. HTTP {response.status_code}: {response.text}", flush=True)
            return False

    except requests.exceptions.RequestException as e:
        print(f">>> [WA ERROR] Koneksi ke server GoWA bermasalah/Timed Out: {e}", flush=True)
        return False