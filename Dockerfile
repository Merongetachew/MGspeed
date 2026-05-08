# 1. Use a stable Python image
FROM python:3.10-slim

# 2. Install system libraries for OpenCV and Video processing
# libgl1-mesa-glx and libglib2.0-0 are essential for OpenCV to run in Docker
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. Set up a non-root user for Hugging Face security
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# 4. Create and set the working directory
WORKDIR $HOME/app

# 5. Install Python libraries
# Ensure 'gunicorn' and 'whitenoise' are in your requirements.txt!
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy your Django code into the container
COPY --chown=user . .

# 7. Hugging Face specific port settings
ENV PORT=7860
EXPOSE 7860

# 8. Start the server using Gunicorn
# Replace 'storefront' with your project folder name if different
CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:7860 storefront.wsgi:application"]
