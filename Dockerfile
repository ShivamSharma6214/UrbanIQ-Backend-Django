# Dockerfile for Django app
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for psycopg2 and Pillow image handling
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	libpq-dev \
	gcc \
	libjpeg-dev \
	zlib1g-dev \
	ffmpeg \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# copy project source
COPY . ./

# copy and install entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
CMD ["gunicorn", "UrbanIQ.wsgi:application", "--bind", "0.0.0.0:8000"]
