import base64
import mimetypes

import requests
from django.template.loader import render_to_string

from produtos.models import Comprador
from .email_service import enviar_email


def enviar_notificacao_produto(produto):
    print("🔥 DISPARANDO EMAIL MARKETING...")

    try:
        compradores = Comprador.objects.filter(
            loja=produto.loja,
            ativo=True,
            usuario__email__isnull=False,
        ).select_related("usuario")

        print(f"EMAIL MARKETING: compradores encontrados = {compradores.count()}")

        emails = []
        for comprador in compradores:
            email = (comprador.usuario.email or "").strip()
            if email and email not in emails:
                emails.append(email)

        print(f"EMAIL MARKETING: emails válidos = {emails}")

        if not emails:
            print("EMAIL MARKETING: nenhum comprador com e-mail encontrado.")
            return

        assunto = f"Novidade na loja {produto.loja.nome}"

        if produto.loja.dominio and produto.loja.dominio not in [
            "nexastoreofficial.com.br",
            "www.nexastoreofficial.com.br",
        ]:
            loja_url = f"https://{produto.loja.dominio}"
        else:
            loja_url = f"https://{produto.loja.slug}.nexastoreofficial.com.br"

        produto_imagem_url = ""
        inline_attachments = []

        if produto.imagem:
            try:
                produto_imagem_url = str(produto.imagem.url).strip()
                print("URL FINAL DA IMAGEM:", produto_imagem_url)

                resposta = requests.get(produto_imagem_url, timeout=20)
                resposta.raise_for_status()

                mime_type = resposta.headers.get("Content-Type") or mimetypes.guess_type(produto_imagem_url)[0] or "image/jpeg"
                extensao = mimetypes.guess_extension(mime_type) or ".jpg"
                nome_arquivo = f"produto{extensao}"

                conteudo_base64 = base64.b64encode(resposta.content).decode("utf-8")

                inline_attachments.append({
                    "content": conteudo_base64,
                    "name": nome_arquivo,
                    "contentType": mime_type,
                    "isInline": True,
                    "inlineId": "produto_img",
                })

                print("EMAIL MARKETING: imagem convertida para inline com sucesso")

            except Exception as e:
                print("EMAIL MARKETING: erro ao preparar imagem inline:", str(e))

        html_body = render_to_string("email/email_produto.html", {
            "produto": produto,
            "loja": produto.loja,
            "loja_url": loja_url,
            "tem_imagem_inline": bool(inline_attachments),
        })

        enviados = 0
        for email in emails:
            try:
                print(f"EMAIL MARKETING: enviando para {email}")
                enviar_email(
                    email,
                    assunto,
                    html_body,
                    inline_attachments=inline_attachments if inline_attachments else None,
                )
                enviados += 1
            except Exception as e:
                print(f"ERRO EMAIL MARKETING para {email}: {str(e)}")

        print(f"EMAIL MARKETING: {enviados} e-mail(s) enviado(s) para o produto {produto.nome}")

    except Exception as e:
        print("ERRO EMAIL MARKETING:", str(e))