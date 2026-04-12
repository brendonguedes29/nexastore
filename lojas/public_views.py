from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, render

from .models import Loja


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
        elif not telefone:
            erro = "Informe o telefone ou WhatsApp."
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
            is_active=True,
        )

        Loja.objects.create(
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

        messages.success(
            request,
            "Conta criada com sucesso. Revise os dados informados e entre no painel com seu e-mail e senha cadastrados."
        )

        return redirect("login_loja")

    return render(
        request,
        "criar_loja.html",
        {
            "valores": valores_iniciais,
        },
    )