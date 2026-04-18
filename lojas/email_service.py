import requests
from django.conf import settings


def enviar_email(destinatario, assunto, html, inline_attachments=None):
    api_key = settings.BREVO_API_KEY.strip()

    print("BREVO API KEY CARREGADA:", bool(api_key))
    print("BREVO API KEY INICIO:", api_key[:12] if api_key else "VAZIA")

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "api-key": api_key,
        "accept": "application/json",
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": "NexaStore",
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

    print("BREVO STATUS:", response.status_code)
    print("BREVO RESPOSTA:", response.text)

    response.raise_for_status()
    return response.json()