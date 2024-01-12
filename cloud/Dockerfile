FROM python:3.6
# Set working directory
WORKDIR /app/cloud/

# Copy current directory
COPY . /app/cloud/

# Copy config_cloud directory
COPY config.yml /app/config_cloud/config.yml

COPY config_flow /app/config_flow

COPY privkey.pem /etc/letsencrypt/live/dev2.virnao.com/privkey.pem

COPY cert.pem /etc/letsencrypt/live/dev2.virnao.com/cert.pem

COPY .sense-o-auth.yaml /root/.sense-o-auth.yaml

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "main.py"]