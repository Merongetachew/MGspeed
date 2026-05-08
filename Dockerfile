# 1. Use the FULL Python image (not slim) to avoid download errors
FROM python:3.10

# 2. Set the working directory
WORKDIR /app

# 3. Install requirements 
# (Make sure 'opencv-python-headless' is in your requirements.txt!)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your project
COPY . .

# 5. The Start Command
# If your folder name is different than 'storefront', change it below
CMD python manage.py collectstatic --noinput && gunicorn storefront.wsgi:application --bind 0.0.0.0:10000
