from django.template.loader import render_to_string
from django.conf import settings

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

        # =========================
        # 🔥 CORREÇÃO DA IMAGEM
        # =========================
        produto_imagem_url = ""

        if produto.imagem:
            try:
                url = produto.imagem.url

                # Se já for absoluta
                if url.startswith("http://") or url.startswith("https://"):
                    produto_imagem_url = url
                else:
                    # Monta URL absoluta (Render)
                    base_url = getattr(settings, "PLATFORM_BASE_URL", "").rstrip("/")
                    produto_imagem_url = f"{base_url}{url}"

            except Exception as e:
                print("ERRO AO GERAR URL DA IMAGEM:", str(e))

        # DEBUG PRA GENTE VER
        print("URL FINAL DA IMAGEM:", produto_imagem_url)

        # =========================
        # TEMPLATE
        # =========================
        html_body = render_to_string("email/email_produto.html", {
            "produto": produto,
            "loja": produto.loja,
            "produto_imagem_url": produto_imagem_url,
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