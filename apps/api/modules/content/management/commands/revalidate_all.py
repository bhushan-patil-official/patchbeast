from django.core.management.base import BaseCommand

from modules.content.services import revalidate_everything


class Command(BaseCommand):
    help = "Refresh every public page now (use when the site looks stale after a change)"

    def handle(self, *args, **opts):
        n = revalidate_everything()
        self.stdout.write(
            self.style.SUCCESS(f"scheduled {n} refresh request(s); pages update within seconds")
        )
