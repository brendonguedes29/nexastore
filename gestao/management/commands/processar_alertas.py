from django.core.management.base import BaseCommand
from gestao.services.alertas import processar_alertas
class Command(BaseCommand):
    help='Gera avisos de vencimento na plataforma e por e-mail via Brevo.'
    def handle(self,*args,**opts):
        total=processar_alertas()
        self.stdout.write(self.style.SUCCESS(f'{total} novo(s) alerta(s) criado(s).'))
