# FROM python:3.9-slim 

# RUN apt-get update && apt-get install -y libpq-dev python3-dev

# COPY requirements.txt /tmp/
# RUN pip install -r /tmp/requirements.txt

# COPY ./src /src
# COPY ./start.sh /start.sh

# WORKDIR /src
# EXPOSE 80
# CMD ["/start.sh"]

FROM python:3.9-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
RUN python manage.py migrate URLShortenerService
EXPOSE 8000

# Start the Django application

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]