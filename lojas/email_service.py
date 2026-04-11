import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY


def enviar_email(destinatario, assunto, html):
    try:
        resend.Emails.send({
            "from": "NexaStore <onboarding@resend.dev>",
            "to": [destinatario],
            "subject": assunto,
            "html": html,
        })
        print("EMAIL ENVIADO COM RESEND")
    except Exception as e:
        print("ERRO RESEND:", e)