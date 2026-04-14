from django.template.loader import render_to_string

from produtos.models import Comprador
from .email_service import enviar_email


def enviar_notificacao_produto(produto):
    try:
        compradores = Comprador.objects.filter(
            loja=produto.loja,
            ativo=True,
            usuario_email_isnull=False
        ).select_related("usuario")

        emails = []
        for comprador in compradores:
            email = (comprador.usuario.email or "").strip()
            if email:
                emails.append(email)

        print(f"EMAIL MARKETING: compradores encontrados = {compradores.count()}")
        print(f"EMAIL MARKETING: emails válidos = {emails}")

        if not emails:
            print("EMAIL MARKETING: nenhum comprador com e-mail encontrado.")
            return

        assunto = f"Novidade na loja {produto.loja.nome}"

        html_body = render_to_string("email/email_produto.html", {
            "produto": produto,
            "loja": produto.loja,
        })

        enviados = 0
        for email in emails:
            try:
                print(f"EMAIL MARKETING: enviando para {email}")
                enviar_email(email, assunto, html_body)
                enviados += 1
            except Exception as e:
                print(f"ERRO EMAIL MARKETING para {email}: {str(e)}")

        print(f"EMAIL MARKETING: {enviados} e-mail(s) enviado(s) para o produto {produto.nome}")

    except Exception as e:
        print("ERRO EMAIL MARKETING:", str(e))