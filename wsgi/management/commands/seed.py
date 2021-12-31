from django.core.management.base import BaseCommand, CommandError

from features.models import Feature
from jobs.models import Job


class Command(BaseCommand):
    help = "Seed database with data"

    def handle(self, *args, **options):
        try:
            Feature.objects.bulk_create(
                [
                    Feature(name="library"),
                    Feature(name="notes"),
                    Feature(name="social"),
                    Feature(name="signup"),
                ]
            )
        except Exception as e:
            raise CommandError(e)
        try:
            Job(name="hackernews").save()
        except Exception as e:
            raise CommandError(e)
        self.stdout.write(self.style.SUCCESS("Successfully seeded database"))
