from django.template.loader import render_to_string

from produtos.models import Comprador
from .email_service import enviar_email


def enviar_notificacao_produto(produto):
    try:
        compradores = Comprador.objects.filter(
            loja=produto.loja,
            ativo=True,
            usuario__email__isnull=False,
        ).select_related("usuario")

        emails = []
        for comprador in compradores:
            email = (comprador.usuario.email or "").strip()
            if email and email not in emails:
                emails.append(email)

        print(f"EMAIL MARKETING: compradores encontrados = {compradores.count()}")
        print(f"EMAIL MARKETING: emails válidos = {emails}")

        if not emails:
            print("EMAIL MARKETING: nenhum comprador com e-mail encontrado.")
            return

        assunto = f"Novidade na loja {produto.loja.nome}"

        # 🔥 CORREÇÃO PRINCIPAL AQUI (URL ABSOLUTA)
        produto_imagem_url = ""
        if produto.imagem:
            try:
                produto_imagem_url = f"https://nexastoreofficial.com.br{produto.imagem.url}"
            except Exception as e:
                print("ERRO AO GERAR URL DA IMAGEM:", str(e))

        # URL da loja
        if produto.loja.dominio and produto.loja.dominio not in [
            "nexastoreofficial.com.br",
            "www.nexastoreofficial.com.br",
        ]:
            loja_url = f"https://{produto.loja.dominio}"
        else:
            loja_url = f"https://{produto.loja.slug}.nexastoreofficial.com.br"

        html_body = render_to_string("email/email_produto.html", {
            "produto": produto,
            "loja": produto.loja,
            "produto_imagem_url": produto_imagem_url,
            "loja_url": loja_url,
        })

        enviados = 0
        for email in emails:
            try:
                print(f"EMAIL MARKETING: enviando para {email}")
                enviar_email(email, assunto, html_body)
                enviados += 1
            except Exception as e:
                print(f"ERRO EMAIL MARKETING para {email}: {str(e)}")

        print(f"EMAIL MARKETING: {enviados} e-mail(s) enviado(s)")
        print(f"EMAIL MARKETING: imagem usada = {produto_imagem_url}")

    except Exception as e:
        print("ERRO EMAIL MARKETING:", str(e))