from platform import python_version

import django
from django.db import connection
from django.db.utils import OperationalError
from django.views import generic


class ScrutinyIndexView(generic.TemplateView):
    template_name = "index.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        return context


class ScrutinyAboutView(generic.TemplateView):
    template_name = "about/index.html"

    @staticmethod
    def database_version() -> str:
        """NB: Hack to 'pretty print' db version"""
        with connection.cursor() as c:
            try:
                c.execute("select version()")
            except OperationalError:
                # fallback to sqlite due to tests
                c.execute("select sqlite_version()")
            full_version = c.fetchone()
        return full_version[0].split("on")[0]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["django_version"] = django.get_version()
        context["python_version"] = python_version()
        context["database_version"] = self.database_version()
        return context
