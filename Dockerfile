FROM python:3.9.1
WORKDIR /
COPY requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]