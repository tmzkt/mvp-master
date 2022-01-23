from django.shortcuts import render
from django.conf import settings
from django.utils.translation import gettext as _
from .models import ArticleModel, InterviewModel, AwardsModel


def publication(request):
    public_article = ArticleModel.objects.all()
    public_interview = InterviewModel.objects.all()
    public_awards = AwardsModel.objects.all()
    return render(request, 'publication/publication.html', {'article':public_article,
                                                            'awards':public_awards,
                                                            'interview':public_interview,
                                                            })
