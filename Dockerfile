
FROM python:3.9-slim


WORKDIR /app


COPY requirements.txt requirements.txt


RUN pip install -r requirements.txt


COPY . .


EXPOSE 5000


ENV FLASK_APP=src/app1.py


CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
