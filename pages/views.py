import mimetypes
import requests

from django.shortcuts import render
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib import messages
from django.utils.translation import gettext as _

from .forms import ApplicationForm, ContactForm, SendingPresentationForm
#from mvp_project.settings.base import PUSHTABLE_API_KEY, PUSHTABLE_PATH, PUSHTABLE_ENDPOINT
# from .tasks import mail_send


def index(request):
    return render(request, 'landing.html')


def privacy(request):
    return render(request, 'privacy.html')


def terms(request):
    return render(request, 'tou.html')


def about(request):
    return render(request, 'about.html')

def additional(request):
    return render(request, 'additional.html')


def antivirus(request):
    return render(request, 'antivirus.html')


def companyMission(request):
    return render(request, 'company-mission.html')


def investorRelations(request):
    return render(request, 'investor-relations.html')


def doctorRelations(request):
    return render(request, 'doctor-relations.html')


def vacancies(request):
    return render(request, 'vacancies.html')

def supportResearch(request):
    return render(request, 'support-research.html')


def contact(request):
    form = ContactForm()

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, _(
                'Your message is accepted! We will contact you shortly.'))
        else:
            messages.add_message(request, messages.ERROR, _(
                'Invalid data specified! Try it again.'))
    return render(request, 'contact.html', {"form": form})

# Вместо перенаправления, показываем пользователю эту же страницу с заявкой, но уведомляем его о том, что заявка принята.


def application(request):
    form = ApplicationForm()

    if request.method == "POST":
        form = ApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, _(
                'Your order is accepted! We will contact you shortly.'))
        else:
            messages.add_message(request, messages.ERROR, _(
                'Invalid data specified! Try it again.'))

    return render(request, "application.html", {"form": form})


def articles(request):
    if request.GET.get('page'):
        if request.GET.get('page') == '':
            next_page = 2
            prev_page = 0
            page = 1
        elif int(request.GET.get('page')) > 0:
            next_page = int(request.GET.get('page')) + 1
            prev_page = int(request.GET.get('page')) - 1
            page = int(request.GET.get('page'))
    else:
        next_page = 2
        prev_page = 0
        page = 1

    PUSHTABLE_LIMIT = '10'
    PUSHTABLE_OFFSET = str(page * int(PUSHTABLE_LIMIT) - int(PUSHTABLE_LIMIT))
    PUSHTABLE_ENDPOINT = settings.PUSHTABLE_ENDPOINT
    PUSHTABLE_PATH = settings.PUSHTABLE_PATH
    PUSHTABLE_API_KEY = settings.PUSHTABLE_API_KEY

    pushtable_request = requests.get(PUSHTABLE_ENDPOINT +
                                     PUSHTABLE_PATH +
                                     '?auth=' + PUSHTABLE_API_KEY +
                                     '&limit=' + PUSHTABLE_LIMIT +
                                     '&offset=' + PUSHTABLE_OFFSET
                                     )

    pushtable_data = pushtable_request.json()

    return render(request, 'articles.html', context={"articles": pushtable_data,
                                                     'next_page': str(next_page),
                                                     'prev_page': str(prev_page),
                                                     'page': str(page)
                                                     })


def article_detail(request, *args, **kwargs):
    PUSHTABLE_DETAIL = kwargs['pubmed_id']
    pushtable_request = requests.get(PUSHTABLE_ENDPOINT +
                                     PUSHTABLE_PATH +
                                     "?auth=" + PUSHTABLE_API_KEY +
                                     '&where={"article_id_pubmed":"' + PUSHTABLE_DETAIL + '"}'
                                     )
    pushtable_data = pushtable_request.json()

    return render(request, 'article_detail.html', context={"article": pushtable_data})


def send_email(request):
    title = request.GET.get('get_parameter_name')
    if request.POST:
        form = SendingPresentationForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            subject = data['title']
            file = data['file']
            name = data['name']
            author_email = data['email']
            text_content = data['message']
            text_content += f'\n\n{author_email}\n{name}'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipients = ['info@intime.digital']
            email = EmailMessage(subject, text_content, from_email, recipients)
            if file:
                email.attach(file.name, file.file.getvalue(), mimetypes.guess_type(file.name)[0])
            email.send()
            # mail_send.delay(data)
            messages.success(request, _('Email sent successfully'))
    form = SendingPresentationForm(initial={'title': title})
    return render(request, 'send_email.html', {'form': form})
