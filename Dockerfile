# 1. Python ka stable image use karein
# 1. Python ka stable image use karein
FROM python:3.10-slim

# 2. System dependencies install karein
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. Working directory set karein
WORKDIR /app

# 4. Requirements copy aur install karein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Poora project code copy karein
COPY . .

# 6. Gunicorn se Flask app run karein
CMD ["gunicorn", "app:app"]