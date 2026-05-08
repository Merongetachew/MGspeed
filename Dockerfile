# 1. Use a lightweight version of Python
FROM python:3.10-slim

# 2. Install the "Video Engines" Render needs for speed analysis
# These libraries (libgl1 and libglib2) help OpenCV process video on a server.
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. Setup the app folder
WORKDIR /app

# 4. Install your requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your folders (storefront, vehiclespeed, etc.)
COPY . .

# 6. Start the web server on the port Render expects (10000)
CMD ["gunicorn", "storefront.wsgi:application", "--bind", "0.0.0.0:10000"]
