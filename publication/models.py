from django.db import models
from django.utils.translation import gettext_lazy as _


class ArticleModel(models.Model):

    name_article_en = models.CharField(_('Add article link in English'), blank=True, max_length=500)
    heading_article_en = models.TextField(_('Add article title in English '), blank=True, default='')
    article_text_en = models.TextField(_('Add article text in English '), blank=True, default='')

    name_article_ru = models.CharField(_('Add article link in Russian'), blank=True, max_length=500)
    heading_article_ru = models.TextField(_('Add article title in Russian '), blank=True, default='')
    article_text_ru = models.TextField(_('Add article text in Russian'), blank=True, default='')

    date_article = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s %s' % (self.heading_article_en, self.heading_article_ru)

    class Meta:
        verbose_name = _('Publication article')
        verbose_name_plural = _('Publication article')


class InterviewModel(models.Model):

    name_interview_en = models.CharField(_('Add interview link in English'), blank=True, max_length=500)
    heading_interview_en = models.TextField(_('Add interview title in English '), blank=True, default='')

    name_interview_ru = models.CharField(_('Add interview link in Russian'), blank=True, max_length=500)
    heading_interview_ru = models.TextField(_('Add interview title in Russian '), blank=True, default='')

    date_interview = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s %s' % (self.heading_interview_en, self.heading_interview_ru)


    class Meta:
        verbose_name = _('Publication interview')
        verbose_name_plural = _('Publication interview')

class AwardsModel(models.Model):

    name_awards_en = models.CharField(_('Add awards link in English'), blank=True, max_length=500)
    heading_awards_en = models.TextField(_('Add awards title in English '), blank=True, default='')
    awards_text_en = models.TextField(_('Add awards text in English '), blank=True, default='')

    name_awards_ru = models.CharField(_('Add awards link in Russian'), blank=True, max_length=500)
    heading_awards_ru = models.TextField(_('Add awards title in Russian '), blank=True, default='')
    awards_text_ru = models.TextField(_('Add awards text in Russian '), blank=True, default='')

    image_awards = models.ImageField(_('Add an award image'), blank=True, upload_to='images/')
    date_awards = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s %s' % (self.awards_text_en, self.awards_text_ru)


    class Meta:
        verbose_name = _('Publication awards')
        verbose_name_plural = _('Publication awards')
