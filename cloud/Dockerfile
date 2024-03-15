FROM python:3.6
# Set working directory
WORKDIR /app/cloud/

# Copy current directory
COPY . /app/cloud/

# Copy config_cloud directory
COPY config.yml /app/config_cloud/config.yml

COPY config_flow /app/config_flow


RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "main.py"]