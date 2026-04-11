import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY

def enviar_email(destinatario, assunto, html):
    resposta = resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": [destinatario],
        "subject": assunto,
        "html": html,
    })
    return resposta