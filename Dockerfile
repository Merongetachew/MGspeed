# 1. Use Python
FROM python:3.10-slim

# 2. Install "Video Engines" (OpenCV needs these to run on a server)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. Set up the app folder
WORKDIR /app

# 4. Install your Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your project files
COPY . .

# 6. Start the website (using port 10000 for Render)
CMD ["gunicorn", "storefront.wsgi:application", "--bind", "0.0.0.0:10000"]
