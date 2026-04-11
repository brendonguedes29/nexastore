import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY


def enviar_email(destinatario, assunto, html):
    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",  # 🔴 SEM nome, só isso
            "to": ["bsg181818@gmail.com"],    # 🔴 FIXO
            "subject": assunto,
            "html": html,
        })
        print("EMAIL ENVIADO COM RESEND")
    except Exception as e:
        print("ERRO RESEND:", e)