# 1. Use the FULL Python image
FROM python:3.10

# 2. Environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. UPDATED: New package names for the graphics fix
RUN apt-get update && apt-get install -y \
    libgl1 \
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
CMD python manage.py collectstatic --noinput && \
    gunicorn storefront.wsgi:application --bind 0.0.0.0:10000
