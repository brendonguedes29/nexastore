import requests
from django.conf import settings


def enviar_email(destinatario, assunto, html):
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
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

    response = requests.post(url, json=payload, headers=headers, timeout=20)

    print("BREVO STATUS:", response.status_code)
    print("BREVO RESPOSTA:", response.text)

    response.raise_for_status()

    return response.json()