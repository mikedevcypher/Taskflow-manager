FROM python:3.12-slim

WORKDIR /app

COPY . /app
RUN pip install PyJWT Flask-Limiter==3.12 flask_compress flask_talisman flask_mail

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENV FLASK_APP=src/main.py
ENV FLASK_ENV=dev
ENV FLASK_DEFAULT_ROUTE=/auth/login

CMD [ "flask", "run", "--host=0.0.0.0" ]
