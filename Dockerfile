from python:3.11.4-slim-bullseye
WORKDIR /app

ENV PYTHONBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["gunicorn", "james_blog.wsgi:application", "--bind", "0.0.0.0:${PORT:-8000}"]