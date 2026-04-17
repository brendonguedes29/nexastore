from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Loja
from .email_service import enviar_email


def landing_page(request):
    return render(request, "landing_page.html")


@transaction.atomic
def criar_loja_publica(request):
    valores_iniciais = {
        "nome_responsavel": "",
        "nome_loja": "",
        "email": "",
        "telefone": "",
    }

    if request.method == "POST":
        nome_responsavel = request.POST.get("nome_responsavel", "").strip()
        nome_loja = request.POST.get("nome_loja", "").strip()
        email = request.POST.get("email", "").strip().lower()
        telefone = request.POST.get("telefone", "").strip()
        senha = request.POST.get("senha", "")
        confirmar_senha = request.POST.get("confirmar_senha", "")

        valores_iniciais = {
            "nome_responsavel": nome_responsavel,
            "nome_loja": nome_loja,
            "email": email,
            "telefone": telefone,
        }

        erro = None

        if not nome_responsavel:
            erro = "Informe o nome do responsável."
        elif not nome_loja:
            erro = "Informe o nome da loja."
        elif not email:
            erro = "Informe o e-mail."
        elif not senha:
            erro = "Informe uma senha."
        elif senha != confirmar_senha:
            erro = "As senhas não coincidem."
        elif User.objects.filter(username=email).exists():
            erro = "Já existe um usuário com esse e-mail."
        elif Loja.objects.filter(nome__iexact=nome_loja).exists():
            erro = "Já existe uma loja com esse nome."

        if erro:
            return render(
                request,
                "criar_loja.html",
                {
                    "erro": erro,
                    "valores": valores_iniciais,
                },
            )

        user = User.objects.create_user(
            username=email,
            email=email,
            password=senha,
            first_name=nome_responsavel,
            is_active=False,
        )

        loja = Loja.objects.create(
            dono=user,
            nome=nome_loja,
            email_comercial=email,
            telefone=telefone,
            ativa=False,
            valor_licenca=49.90,
            status_licenca="pendente",
            banner_titulo="+ PRODUTOS NA SUA LOJA",
            banner_subtitulo="Compre com praticidade e encontre tudo em um só lugar.",
            banner_botao_texto="Comprar agora",
            banner_botao_link="#produtos",
            banner_cor_inicio="#16a34a",
            banner_cor_fim="#2563eb",
            texto_busca="O que você procura?",
        )

        # domínio padrão automático da loja
        loja.dominio = f"{loja.slug}.nexastoreofficial.com.br"
        loja.save(update_fields=["dominio", "atualizado_em"])

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        link = request.build_absolute_uri(
            reverse("ativar_conta", kwargs={"uidb64": uid, "token": token})
        )

        html_body = render_to_string(
            "email/ativar_conta.html",
            {
                "nome": nome_responsavel,
                "link_ativacao": link,
            },
        )

        try:
            enviar_email(
                email,
                "Ative sua conta na NexaStore",
                html_body,
            )

            messages.success(
                request,
                "Conta criada com sucesso. Abra seu e-mail e clique no link de ativação para liberar o acesso ao painel.",
            )

        except Exception as e:
            print("ERRO AO ENVIAR EMAIL:", e)
            messages.warning(
                request,
                "Conta criada, mas houve falha no envio do e-mail de ativação. Tente novamente mais tarde.",
            )

        return redirect("login_loja")

    return render(
        request,
        "criar_loja.html",
        {
            "valores": valores_iniciais,
        },
    )