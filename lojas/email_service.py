import requests
from django.conf import settings


def enviar_email(destinatario, assunto, html, inline_attachments=None):
    api_key = settings.BREVO_API_KEY.strip()

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "api-key": api_key,
        "accept": "application/json",
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": "Nexa Gestão",
            "email": settings.DEFAULT_FROM_EMAIL,
        },
        "to": [
            {"email": destinatario}
        ],
        "subject": assunto,
        "htmlContent": html,
    }

    if inline_attachments:
        payload["attachment"] = inline_attachments

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    response.raise_for_status()
    return response.json()