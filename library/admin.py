from django.contrib import admin

from library.models import Article, Tag


admin.site.register(Article)
admin.site.register(Tag)
