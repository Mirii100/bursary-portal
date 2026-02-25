from django.apps import AppConfig


class BursaryConfig(AppConfig):
    name = 'bursary'

    def ready(self):
        import bursary.signals
