from django.contrib import admin
from .models import ArticleModel, InterviewModel, AwardsModel


class ArticleModelAdmin(admin.ModelAdmin):

    list_display = ('heading_article_en', 'name_article_en', 'heading_article_ru', 'name_article_ru', 'date_article')
    list_filter = ('date_article', 'heading_article_en', 'heading_article_ru')
    date_hierarchy = ('date_article')
    search_fields = ('heading_article_en', 'heading_article_ru')
    ordering = ['-date_article']
    list_display_links = ('heading_article_en', 'heading_article_ru')

admin.site.register(ArticleModel, ArticleModelAdmin)


class InterviewModelAdmin(admin.ModelAdmin):

    list_display = ('heading_interview_en', 'name_interview_en', 'heading_interview_ru', 'name_interview_ru', 'date_interview')
    list_filter = ('date_interview', 'heading_interview_en', 'heading_interview_ru')
    date_hierarchy = ('date_interview')
    search_fields = ('heading_interview_en', 'heading_interview_ru')
    ordering = ['-date_interview']
    list_display_links = ('heading_interview_en', 'heading_interview_ru')

admin.site.register(InterviewModel, InterviewModelAdmin)


class AwardsModelAdmin(admin.ModelAdmin):

    list_display = ('heading_awards_en', 'name_awards_en', 'heading_awards_ru', 'name_awards_ru', 'date_awards')
    list_filter = ('date_awards', 'heading_awards_en', 'heading_awards_ru')
    date_hierarchy = ('date_awards')
    search_fields = ('heading_awards_en', 'heading_awards_ru')
    ordering = ['-date_awards']
    list_display_links = ('heading_awards_en', 'heading_awards_ru')

admin.site.register(AwardsModel, AwardsModelAdmin)
