import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from apps.ai_engine.services.learning_worker_service import LearningWorkerService


class Command(BaseCommand):
    help = "Resolve forecasts and simulated paper exits. Never calls a live-order API."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--interval", type=int, default=60)

    def handle(self, *args, **options):
        while True:
            close_old_connections()
            try:
                self.stdout.write(str(LearningWorkerService.tick()))
            except Exception as exc:
                self.stderr.write(f"Learning worker deferred ({type(exc).__name__}).")
                if options["once"]:
                    raise
            if options["once"]:
                return
            time.sleep(max(30, options["interval"]))

