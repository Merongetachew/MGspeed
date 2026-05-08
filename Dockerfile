# 1. Use the FULL Python image
FROM python:3.10

# 2. Set environment variables to keep Python snappy
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. FIX THE ERROR: Install system libraries for OpenCV/YOLO
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 4. Set the working directory
WORKDIR /app

# 5. Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy your project
COPY . .

# 7. Collect static files and Start Command
# Using 10000 because that is the default Render port
CMD python manage.py collectstatic --noinput && \
    gunicorn storefront.wsgi:application --bind 0.0.0.0:10000
