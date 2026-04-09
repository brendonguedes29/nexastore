import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY

def enviar_email_html(destinatario, assunto, html):
    params = {
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": [destinatario],
        "subject": assunto,
        "html": html,
    }
    return resend.Emails.send(params)