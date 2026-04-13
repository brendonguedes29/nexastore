from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail

from produtos.models import Comprador


def enviar_notificacao_produto(produto):
    try:
        compradores = Comprador.objects.filter(
            loja=produto.loja,
            ativo=True,
            usuario_email_isnull=False
        )

        emails = [c.usuario.email for c in compradores if c.usuario.email]

        if not emails:
            return

        assunto = f"🔥 Novidade na loja {produto.loja.nome}"

        contexto = {
            "produto": produto,
            "loja": produto.loja,
        }

        mensagem_html = render_to_string("email_produto.html", contexto)

        send_mail(
            subject=assunto,
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=emails,
            html_message=mensagem_html,
            fail_silently=True,
        )

    except Exception as e:
        print("ERRO EMAIL MARKETING:", str(e))