# 使用官方 Python 3.12 映像作為基礎
FROM python:3.12-slim

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴 (如果您的 Python 套件需要編譯)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴需求檔案並安裝
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 複製整個專案到工作目錄
COPY .. .

# (Gunicorn 啟動命令不變)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reload", "run:app"]