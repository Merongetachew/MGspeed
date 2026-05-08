# 1. Use Python
FROM python:3.10-slim

# 2. The Fix: We add '--fix-missing' and an extra update step
RUN apt-get update --fix-missing && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Setup the rest as before
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# 4. Start command
CMD ["gunicorn", "storefront.wsgi:application", "--bind", "0.0.0.0:10000"]
