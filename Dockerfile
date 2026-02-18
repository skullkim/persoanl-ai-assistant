FROM python:3.11-slim

WORKDIR /app

# C 확장 빌드 의존성 설치 → pip install → 빌드 의존성 제거
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc curl && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove gcc curl && \
    rm -rf /var/lib/apt/lists/*

# supercronic 설치 (컨테이너 전용 경량 cron)
ARG TARGETARCH
ADD https://github.com/aptible/supercronic/releases/download/v0.2.33/supercronic-linux-${TARGETARCH} /usr/local/bin/supercronic
RUN chmod +x /usr/local/bin/supercronic

# 소스 코드 복사
COPY . .

RUN mkdir -p /app/data
