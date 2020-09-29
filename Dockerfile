FROM python:3.6.5

WORKDIR /usr/src/app

# install supervisord
RUN apt-get update && apt-get install -y supervisor

# copy requirements and install (so that changes to files do not mean rebuild cannot be cached)
COPY . /www
WORKDIR /www
RUN pip install -r requirements.txt

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
# expose port 80 of the container (HTTP port, change to 443 for HTTPS)
EXPOSE 5001

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# needs to be set else Celery gives an error (because docker runs commands inside container as root)
ENV C_FORCE_ROOT=1
# run supervisord
CMD ["/usr/bin/supervisord"]