from __future__ import absolute_import, unicode_literals
import json
import requests
import logging

from celery import shared_task

from django.conf import settings
from django.core.mail import send_mail

from rest_framework.exceptions import ValidationError
from rest_framework import response, status
from . import app_settings, serializers, count

logger = logging.getLogger('django')


# sending a warning letter
@shared_task
def warning_mail_send(user_email):
    text_content = 'we recorded an attempt to log in to your account. If it was you, then simply ' \
                   'ignore this letter. If it wasn’t you - contact the site administration as soon as possible.'
    subject = 'Attempt to log in to your account'
    from_email = settings.DEFAULT_FROM_EMAIL
    # receive warning mail
    mail_sent = send_mail(subject, text_content, from_email, [user_email])

    return mail_sent


@shared_task
def post_health_data(data_dict):
    logger.info("Task | post_health_data | Data came [{}]".format(data_dict))
    data = count.count_risk(data_dict)
    logger.info("Task | post_health_data | Sent Dashboard for user: {}".format(data_dict["user_email"]))

    try:
        # data = json.loads(r)
        serializer = serializers.ResultSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            logger.info("Task | post_health_data | Save result")
        else:
            logger.exception("Task | post_health_data | Exception! Serializer invalid!")
            raise ValidationError
    except:
        logger.exception("Task | post_health_data | Exception")


@shared_task
def reset_pass_mail_send(post_url, post_data):
    logger.info("URL: {}, Data: {}".format(post_url, post_data))
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/39.0.2171.95 Safari/537.36',
               'Content-type': 'application/json', 'Accept': '*/*'}
    r = requests.post(post_url, data=json.dumps(post_data), headers=headers)
    logger.info(r.status_code)


