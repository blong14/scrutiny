from django.contrib import admin

from notes.models import Note, Project

admin.site.register(Note)
admin.site.register(Project)
