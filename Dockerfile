FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE mvp_project.settings.docker

#Set dependence 
COPY requirements.txt /usr/src/app/
RUN pip install --upgrade pip
RUN pip install -r /usr/src/app/requirements.txt

#Create and copy directory  
WORKDIR /usr/src/app
COPY . /usr/src/app
RUN mkdir -p /usr/src/app/logs/django

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
