FROM python:3.11-slim

# 创建非 root 用户(Hugging Face Spaces 以 UID 1000 运行)
RUN useradd -m -u 1000 user

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend

# 数据库写到容器内可写目录,赋予运行用户权限
ENV APP_DB_PATH=/data/applications.db
RUN mkdir -p /data && chown -R user:user /app /data

USER user

EXPOSE 8000
WORKDIR /app/backend
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
