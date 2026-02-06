FROM python:3.10-slim

# ===== TIMEZONE FIX =====
ENV TZ=Asia/Jakarta
RUN apt update && \
    apt install -y tzdata iputils-ping ffmpeg libsm6 libxext6 git && \
    ln -snf /usr/share/zoneinfo/Asia/Jakarta /etc/localtime && \
    echo Asia/Jakarta > /etc/timezone && \
    apt clean && rm -rf /var/lib/apt/lists/*
# =======================

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
