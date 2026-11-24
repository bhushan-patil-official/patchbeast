from django.core.management.base import BaseCommand, CommandError

from modules.platform.services import kill_switch_on, set_kill_switch


class Command(BaseCommand):
    help = "killswitch on|off|status — pause/resume fetching, LLM and auto-publish"

    def add_arguments(self, parser):
        parser.add_argument("state", choices=["on", "off", "status"])

    def handle(self, *args, state, **opts):
        if state == "status":
            self.stdout.write("ON (pipeline paused)" if kill_switch_on() else "off")
            return
        set_kill_switch(state == "on")
        self.stdout.write(self.style.WARNING(f"kill switch {state.upper()}"))
