FROM python:3.9 

WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./

EXPOSE 8000

CMD ["python", "server.py"]