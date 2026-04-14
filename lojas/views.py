from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import json
import urllib.parse
import urllib.request
import openpyxl
import requests

from urllib.parse import quote
from collections import defaultdict

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.sites.shortcuts import get_current_site

from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.db import transaction

from django.urls import reverse
from django.core.mail import send_mail

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .email_service import enviar_email
from .marketing_email import enviar_notificacao_produto
from django.db.models import F, Sum

from .models import Loja
from .forms import LojaForm, LojaDadosForm, LojaVitrineForm

from produtos.models import (
    Produto,
    ProdutoImagem,
    Pedido,
    Categoria,
    MovimentacaoEstoque,
    Comprador,
    ConfigFrete,
    FaixaFrete,
)

from produtos.forms import (
    ProdutoForm,
    CategoriaForm,
    CadastroCompradorForm,
    ConfigFreteForm,
    FaixaFreteForm,
)


def ativar_ou_renovar_licenca(loja, dias=30):
    agora = timezone.now()

    if loja.data_vencimento_licenca and loja.data_vencimento_licenca > agora:
        base = loja.data_vencimento_licenca
    else:
        base = agora

    loja.status_licenca = "ativa"
    loja.data_ultimo_pagamento = agora
    loja.data_vencimento_licenca = base + timedelta(days=dias)
    loja.ativa = True
    loja.save()


def escolher_acesso(request):
    next_url = request.GET.get("next") or request.POST.get("next") or "/"

    lojas = Loja.objects.filter(
        ativa=True,
        status_licenca="ativa"
    ).order_by("nome")

    lojas_por_tipo = defaultdict(list)

    for loja in lojas:
        lojas_por_tipo[loja.get_tipo_loja_display()].append(loja)

    if request.method == "POST":
        tipo_acesso = request.POST.get("tipo_acesso")
        slug_loja = (request.POST.get("slug_loja") or "").strip()

        if tipo_acesso == "lojista":
            destino = "/login/"
            if next_url and next_url != "/":
                destino += f"?next={quote(next_url)}"
            return redirect(destino)

        if tipo_acesso == "consumidor":
            if not slug_loja:
                messages.error(request, "Selecione uma loja para entrar como consumidor.")
                return render(request, "escolher_acesso.html", {
                    "next_url": next_url,
                    "lojas_por_tipo": dict(lojas_por_tipo),
                })

            return redirect(f"/loja/{slug_loja}/")

    return render(request, "escolher_acesso.html", {
        "next_url": next_url,
        "lojas_por_tipo": dict(lojas_por_tipo),
    })

def mp_get(url, token):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
        },
        method="GET",
    )

    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def get_loja_do_dono(request):
    if not request.user.is_authenticated:
        return None

    loja = Loja.objects.filter(dono=request.user).first()

    if loja:
        loja.verificar_licenca()

    return loja


def get_comprador_logado(request, loja=None):
    if not request.user.is_authenticated:
        return None

    compradores = Comprador.objects.filter(usuario=request.user, ativo=True)

    if loja is not None:
        compradores = compradores.filter(loja=loja)

    return compradores.first()


def loja_com_licenca_bloqueada(loja):
    if not loja:
        return True

    loja.verificar_licenca()

    if loja.status_licenca in ["pendente", "vencida"]:
        return True

    if not loja.ativa:
        return True

    return False


def bloquear_acesso_se_licenca_inativa(request, loja):
    loja.verificar_licenca()

    if loja.status_licenca in ["pendente", "vencida"] or not loja.ativa:
        return redirect("licenca_bloqueada")

    return None

def plano_permite_exportar_excel(loja):
    plano = plano_nome_normalizado(loja)
    return plano in ["intermediario", "premium"]


def plano_permite_relatorios(loja):
    plano = plano_nome_normalizado(loja)
    return plano in ["intermediario", "premium"]


def plano_permite_vitrine(loja):
    plano = plano_nome_normalizado(loja)
    return plano in ["intermediario", "premium"]
def plano_permite_cartao(loja):
    plano = plano_nome_normalizado(loja)
    return plano in ["intermediario", "premium"]


def home(request):
    primeira_loja = Loja.objects.order_by("id").first()
    if primeira_loja:
        return redirect("loja", slug=primeira_loja.slug)
    return redirect("login_loja")


def aplicar_filtro_data(queryset, data_inicio, data_fim):
    if data_inicio:
        data_inicio_convertida = parse_date(data_inicio)
        if data_inicio_convertida:
            queryset = queryset.filter(data__date__gte=data_inicio_convertida)

    if data_fim:
        data_fim_convertida = parse_date(data_fim)
        if data_fim_convertida:
            queryset = queryset.filter(data__date__lte=data_fim_convertida)

    return queryset


def total_itens_carrinho(request):
    carrinho = request.session.get("carrinho", {})
    return sum(carrinho.values())


def calcular_frete_checkout(loja, estado_entrega, distancia_km=None, retirada_na_loja=False):
    config = ConfigFrete.objects.filter(loja=loja).first()

    if not config:
        return Decimal("0.00")

    if retirada_na_loja and config.retirada_loja:
        return Decimal("0.00")

    if not retirada_na_loja and not config.entrega_ativa:
        return None

    estado_loja = (config.estado_origem or "").strip().lower()
    estado_cliente = (estado_entrega or "").strip().lower()

    if estado_cliente and estado_loja and estado_cliente != estado_loja:
        return config.valor_fora_estado or Decimal("0.00")

    if distancia_km is None or distancia_km == "":
        return None

    try:
        distancia_km = Decimal(str(distancia_km))
    except Exception:
        return None

    faixa = (
        FaixaFrete.objects.filter(
            loja=loja,
            ativo=True,
            km_inicial__lte=distancia_km,
            km_final__gte=distancia_km,
        )
        .order_by("km_inicial")
        .first()
    )

    if faixa:
        return faixa.valor

    return None

@transaction.atomic
def confirmar_pagamento_por_referencia(referencia):
    pedidos = Pedido.objects.filter(referencia_pagamento=referencia)

    if not pedidos.exists():
        return False

    for pedido in pedidos:
        pedido.status_pagamento = "pago"
        pedido.status = "aguardando_envio"
        pedido.data_pagamento = timezone.now()
        pedido.save()
        baixar_estoque_do_pedido(pedido)
        enviar_email_status_pedido(pedido)

    return True


@login_required
def logout_loja(request):
    logout(request)
    return redirect("login_loja")
def produto_view(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id, ativo=True)
    loja = produto.loja
    comprador_logado = get_comprador_logado(request, loja)
    imagens_extras = produto.imagens_extras.all()

    return render(request, "produto.html", {
        "produto": produto,
        "loja": loja,
        "comprador_logado": comprador_logado,
        "imagens_extras": imagens_extras,
        "total_itens_carrinho": total_itens_carrinho(request),
    })


def loja_view(request, slug):
    loja = get_object_or_404(Loja, slug=slug)

    loja.verificar_licenca()

    if loja.status_licenca in ["pendente", "vencida"] or not loja.ativa:
        return HttpResponse("Loja temporariamente indisponível.", status=403)

    busca = request.GET.get("busca", "").strip()
    categoria = request.GET.get("categoria")
    tipo = request.GET.get("tipo")

    produtos = Produto.objects.filter(loja=loja, ativo=True)

    if categoria:
        produtos = produtos.filter(categoria_id=categoria)

    if busca:
        produtos = produtos.filter(nome__icontains=busca)

    if tipo == "promocao":
        produtos = produtos.filter(percentual_promocao__gt=0)
    elif tipo == "destaque":
        produtos = produtos.filter(em_destaque=True)
    elif tipo == "novo":
        produtos = produtos.filter(produto_novo=True)

    categorias_lista = Categoria.objects.filter(loja=loja).order_by("nome")
    comprador_logado = get_comprador_logado(request, loja)
    produtos_ordenados = produtos.order_by("-id")

    return render(request, "loja.html", {
        "loja": loja,
        "produtos": produtos_ordenados,
        "categorias": categorias_lista,
        "categoria_selecionada": categoria,
        "busca": busca,
        "tipo": tipo,
        "comprador_logado": comprador_logado,
        "total_itens_carrinho": total_itens_carrinho(request),
    })


def login_comprador(request, slug):
    loja = get_object_or_404(Loja, slug=slug)

    loja.verificar_licenca()

    if loja.status_licenca in ["pendente", "vencida"] or not loja.ativa:
        return HttpResponse("Loja temporariamente indisponível.", status=403)

    erro = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:

            # 🔥 BLOQUEIO AQUI
            if not user.is_active:
                erro = "Confirme seu e-mail antes de entrar."
            else:
                comprador = Comprador.objects.filter(usuario=user, loja=loja, ativo=True).first()

                if comprador:
                    login(request, user)
                    request.session["ultima_loja_slug"] = loja.slug
                    return redirect("loja", slug=loja.slug)

        else:
            erro = "Usuário ou senha inválidos."

    return render(request, "login_comprador.html", {
        "loja": loja,
        "erro": erro,
    })


def cadastro_comprador(request, slug):
    loja = get_object_or_404(Loja, slug=slug)

    loja.verificar_licenca()

    if loja.status_licenca in ["pendente", "vencida"] or not loja.ativa:
        return HttpResponse("Loja temporariamente indisponível.", status=403)

    mensagem = None
    erro = None

    if request.method == "POST":
        form = CadastroCompradorForm(request.POST)

        if form.is_valid():
            try:
                user = User.objects.create_user(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password1"],
                    first_name=form.cleaned_data["nome"],
                    is_active=False
                )

                Comprador.objects.create(
                    usuario=user,
                    loja=loja,
                    telefone=form.cleaned_data["telefone"],
                    ativo=True,
                )

                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                link = request.build_absolute_uri(
                    reverse("ativar_conta", kwargs={"uidb64": uid, "token": token})
                )

                assunto = f"Ative sua conta em {loja.nome}"

                html_body = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; background:#f4f6fb; padding:24px;">
                        <div style="max-width:600px; margin:0 auto; background:#ffffff; border-radius:18px; padding:32px; border:1px solid #e5e7eb;">
                            <h2 style="margin-top:0; color:#111827;">Confirme sua conta</h2>
                            <p>Olá, {user.first_name}.</p>
                            <p>Sua conta de comprador foi criada com sucesso em <strong>{loja.nome}</strong>.</p>
                            <p>Para ativar seu acesso, clique no botão abaixo:</p>

                            <p style="margin:28px 0;">
                                <a href="{link}" style="background:#06b6d4; color:#ffffff; text-decoration:none; padding:14px 22px; border-radius:12px; font-weight:bold;">
                                    Ativar minha conta
                                </a>
                            </p>

                            <p>Se preferir, use este link:</p>
                            <p><a href="{link}">{link}</a></p>

                            <p style="margin-top:28px; color:#64748b;">
                                Se você não solicitou este cadastro, ignore esta mensagem.
                            </p>
                        </div>
                    </body>
                </html>
                """

                enviar_email(
                    user.email,
                    assunto,
                    html_body,
                )

                mensagem = "Conta criada com sucesso. Enviamos um link de ativação para o seu e-mail. Após ativar, você poderá entrar normalmente."
                form = CadastroCompradorForm()

            except Exception as e:
                print("ERRO AO CADASTRAR COMPRADOR:", str(e))
                erro = f"Erro ao criar conta: {str(e)}"

    else:
        form = CadastroCompradorForm()

    return render(request, "cadastro_comprador.html", {
        "loja": loja,
        "form": form,
        "mensagem": mensagem,
        "erro": erro,
    })


def logout_comprador(request):
    slug = request.session.get("ultima_loja_slug")
    logout(request)

    if slug:
        return redirect("loja", slug=slug)
    return redirect("home")

@login_required
def excluir_produto(request, produto_id):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    if loja_com_licenca_bloqueada(loja):
        return redirect("painel_loja")

    produto = get_object_or_404(Produto, id=produto_id, loja=loja)

    if request.method == "POST":
        produto.delete()
        return redirect("lista_produtos_painel")

    return render(request, "excluir_produto.html", {
        "loja": loja,
        "produto": produto,
    })


@login_required
def meus_pedidos(request):
    comprador = get_comprador_logado(request)

    if not comprador:
        return redirect("home")

    pedidos_lista = (
        Pedido.objects.filter(comprador=comprador)
        .select_related("produto", "loja")
        .order_by("-data")
    )

    return render(request, "meus_pedidos.html", {
        "loja": comprador.loja,
        "comprador_logado": comprador,
        "pedidos": pedidos_lista,
        "total_itens_carrinho": total_itens_carrinho(request),
    })


def adicionar_carrinho(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id, ativo=True)
    carrinho = request.session.get("carrinho", {})

    quantidade = int(request.POST.get("quantidade", 1))
    if quantidade < 1:
        quantidade = 1

    produto_id = str(produto_id)

    if produto_id in carrinho:
        carrinho[produto_id] += quantidade
    else:
        carrinho[produto_id] = quantidade

    request.session["carrinho"] = carrinho
    request.session["ultima_loja_slug"] = produto.loja.slug

    return redirect("ver_carrinho")
def ver_carrinho(request):
    carrinho = request.session.get("carrinho", {})
    itens = []
    total = Decimal("0.00")
    loja = None

    for produto_id, quantidade in carrinho.items():
        produto = get_object_or_404(Produto, id=produto_id, ativo=True)

        if loja is None:
            loja = produto.loja

        subtotal = produto.preco * quantidade
        total += subtotal

        itens.append({
            "produto": produto,
            "quantidade": quantidade,
            "subtotal": subtotal,
        })

    if loja is None:
        slug = request.session.get("ultima_loja_slug")
        if slug:
            loja = Loja.objects.filter(slug=slug).first()

    comprador_logado = get_comprador_logado(request, loja) if loja else None

    return render(request, "carrinho.html", {
        "itens": itens,
        "total": total,
        "loja": loja,
        "comprador_logado": comprador_logado,
        "total_itens_carrinho": total_itens_carrinho(request),
    })


def remover_carrinho(request, produto_id):
    carrinho = request.session.get("carrinho", {})
    produto_id = str(produto_id)

    if produto_id in carrinho:
        del carrinho[produto_id]

    request.session["carrinho"] = carrinho
    request.session.modified = True

    return redirect("ver_carrinho")


def atualizar_carrinho(request):
    if request.method == "POST":
        carrinho = request.session.get("carrinho", {})

        for key, value in request.POST.items():
            if key.startswith("qtd_"):
                produto_id = key.replace("qtd_", "")
                try:
                    quantidade = int(value)
                except (ValueError, TypeError):
                    quantidade = 1

                if quantidade <= 0:
                    carrinho.pop(produto_id, None)
                else:
                    carrinho[produto_id] = quantidade

        request.session["carrinho"] = carrinho
        request.session.modified = True

        if request.POST.get("ir_checkout") == "1":
            return redirect("checkout")

    return redirect("ver_carrinho")


def checkout(request):
    carrinho = request.session.get("carrinho", {})
    itens = []
    subtotal_geral = Decimal("0.00")
    loja = None

    for produto_id, quantidade in carrinho.items():
        produto = get_object_or_404(Produto, id=produto_id, ativo=True)

        if loja is None:
            loja = produto.loja

        subtotal = produto.preco * quantidade
        subtotal_geral += subtotal

        itens.append({
            "produto": produto,
            "quantidade": quantidade,
            "subtotal": subtotal,
        })

    if not itens:
        pedido_pendente = None

        if request.user.is_authenticated:
            comprador_pendente = Comprador.objects.filter(
                usuario=request.user,
                ativo=True
            ).first()

            if comprador_pendente:
                pedido_pendente = Pedido.objects.filter(
                    comprador=comprador_pendente,
                    status="pendente",
                    status_pagamento__in=["aguardando", "confirmacao"]
                ).order_by("-data").first()

        if pedido_pendente:
            messages.warning(
                request,
                "Pedido pendente. Finalize no histórico."
            )
            return redirect("meus_pedidos")

        messages.warning(request, "Seu carrinho está vazio.")
        return redirect("ver_carrinho")

    comprador = Comprador.objects.filter(
        usuario=request.user,
        loja=loja,
        ativo=True
    ).first()

    if not comprador:
        return redirect("login_comprador", slug=loja.slug)

    config_frete = ConfigFrete.objects.filter(loja=loja).first()

    frete = Decimal("0.00")
    total_geral = subtotal_geral

    if request.method == "POST":
        nome_cliente = request.POST.get("nome_cliente", "").strip()
        telefone = request.POST.get("telefone", "").strip()
        forma_pagamento = request.POST.get("forma_pagamento", "pix").strip().lower()
        tipo_cartao = request.POST.get("tipo_cartao", "").strip().lower()
        observacao = request.POST.get("observacao", "").strip()

        cep_entrega = request.POST.get("cep_entrega", "").strip()
        rua_entrega = request.POST.get("rua_entrega", "").strip()
        numero_entrega = request.POST.get("numero_entrega", "").strip()
        complemento_entrega = request.POST.get("complemento_entrega", "").strip()
        bairro_entrega = request.POST.get("bairro_entrega", "").strip()
        cidade_entrega = request.POST.get("cidade_entrega", "").strip()
        estado_entrega = request.POST.get("estado_entrega", "").strip()

        tipo_entrega = request.POST.get("tipo_entrega", "entrega").strip().lower()
        retirada_na_loja = tipo_entrega == "retirada"

        distancia_km_raw = request.POST.get("distancia_km", "").strip()
        distancia_km = Decimal("0.00")

        if distancia_km_raw:
            try:
                distancia_km = Decimal(distancia_km_raw.replace(",", "."))
            except Exception:
                return render(request, "checkout.html", {
                    "erro": "Distância inválida para cálculo do frete.",
                    "itens": itens,
                    "subtotal_geral": subtotal_geral,
                    "frete": frete,
                    "total": total_geral,
                    "loja": loja,
                    "comprador": comprador,
                    "config_frete": config_frete,
                })

        endereco = f"{rua_entrega}, {numero_entrega}, {bairro_entrega}, {cidade_entrega} - {estado_entrega}, CEP: {cep_entrega}"

        if forma_pagamento != "cartao":
            tipo_cartao = ""

        if not nome_cliente or not telefone:
            return render(request, "checkout.html", {
                "erro": "Preencha nome e telefone.",
                "itens": itens,
                "subtotal_geral": subtotal_geral,
                "frete": frete,
                "total": total_geral,
                "loja": loja,
                "comprador": comprador,
                "config_frete": config_frete,
            })

        if not retirada_na_loja:
            if not all([rua_entrega, numero_entrega, cidade_entrega, estado_entrega]):
                return render(request, "checkout.html", {
                    "erro": "Preencha todos os campos obrigatórios de entrega.",
                    "itens": itens,
                    "subtotal_geral": subtotal_geral,
                    "frete": frete,
                    "total": total_geral,
                    "loja": loja,
                    "comprador": comprador,
                    "config_frete": config_frete,
                })

            frete_calculado = calcular_frete_checkout(
                loja=loja,
                estado_entrega=estado_entrega,
                distancia_km=distancia_km,
                retirada_na_loja=False,
            )

            if frete_calculado is None:
                return render(request, "checkout.html", {
                    "erro": "Não foi encontrada uma faixa de frete para essa distância.",
                    "itens": itens,
                    "subtotal_geral": subtotal_geral,
                    "frete": frete,
                    "total": total_geral,
                    "loja": loja,
                    "comprador": comprador,
                    "config_frete": config_frete,
                })

            frete = frete_calculado
        else:
            frete = calcular_frete_checkout(
                loja=loja,
                estado_entrega=estado_entrega,
                distancia_km=Decimal("0.00"),
                retirada_na_loja=True,
            )

            if frete is None:
                return render(request, "checkout.html", {
                    "erro": "Retirada na loja não está disponível.",
                    "itens": itens,
                    "subtotal_geral": subtotal_geral,
                    "frete": Decimal("0.00"),
                    "total": subtotal_geral,
                    "loja": loja,
                    "comprador": comprador,
                    "config_frete": config_frete,
                })

            cep_entrega = ""
            rua_entrega = "RETIRADA NA LOJA"
            numero_entrega = ""
            complemento_entrega = ""
            bairro_entrega = ""
            cidade_entrega = ""
            estado_entrega = ""
            endereco = "RETIRADA NA LOJA"

        total_geral = subtotal_geral + frete

        quantidade_itens = len(itens)
        frete_rateado = frete / quantidade_itens if quantidade_itens > 0 else Decimal("0.00")

        referencia_pagamento = uuid4().hex[:20].upper()

        for item in itens:
            valor_total_item = item["subtotal"] + frete_rateado

            Pedido.objects.create(
                produto=item["produto"],
                loja=item["produto"].loja,
                comprador=comprador,
                nome_cliente=nome_cliente,
                telefone=telefone,
                endereco=endereco,
                forma_pagamento=forma_pagamento,
                tipo_cartao=tipo_cartao,
                observacao=observacao,
                cep_entrega=cep_entrega,
                rua_entrega=rua_entrega,
                numero_entrega=numero_entrega,
                complemento_entrega=complemento_entrega,
                bairro_entrega=bairro_entrega,
                cidade_entrega=cidade_entrega,
                estado_entrega=estado_entrega,
                distancia_km=distancia_km,
                valor_frete=frete_rateado,
                valor_total=valor_total_item,
                status_pagamento="aguardando",
                referencia_pagamento=referencia_pagamento,
                quantidade=item["quantidade"],
                status="pendente",
            )

        request.session["carrinho"] = {}
        request.session.modified = True

        return redirect("pagina_pagamento", referencia=referencia_pagamento)

    return render(request, "checkout.html", {
        "itens": itens,
        "subtotal_geral": subtotal_geral,
        "frete": frete,
        "total": total_geral,
        "loja": loja,
        "comprador": comprador,
        "comprador_logado": comprador,
        "config_frete": config_frete,
        "total_itens_carrinho": total_itens_carrinho(request),
    })
@login_required
def pagina_pagamento(request, referencia):
    pedidos_lista = Pedido.objects.filter(
        referencia_pagamento=referencia
    ).order_by("id")

    if not pedidos_lista.exists():
        return redirect("home")

    pedido = pedidos_lista.first()
    total_pedido = sum((p.valor_total for p in pedidos_lista), Decimal("0.00"))

    if pedido.status_pagamento == "pago":
        return redirect("pagamento_sucesso", referencia=referencia)

    email_pagador = "cliente@exemplo.com"
    if pedido.comprador and pedido.comprador.usuario and pedido.comprador.usuario.email:
        email_pagador = pedido.comprador.usuario.email

    return render(request, "pagamento.html", {
        "pedido": pedido,
        "referencia": pedido.referencia_pagamento,
        "total_pedido": total_pedido,
        "forma_pagamento": (pedido.forma_pagamento or "").strip().lower(),
        "tipo_cartao": (pedido.tipo_cartao or "").strip().lower(),
        "mp_public_key": getattr(settings, "MERCADOPAGO_PUBLIC_KEY", ""),
        "email_pagador": email_pagador,
    })


@login_required
def pagina_pagamento_cartao(request, referencia):
    pedidos_lista = Pedido.objects.filter(
        referencia_pagamento=referencia
    ).order_by("id")

    if not pedidos_lista.exists():
        return redirect("home")

    pedido = pedidos_lista.first()
    total = sum((p.valor_total for p in pedidos_lista), Decimal("0.00"))

    if pedido.status_pagamento == "pago":
        return redirect("pagamento_sucesso", referencia=referencia)

    if pedido.forma_pagamento != "cartao":
        return redirect("pagina_pagamento", referencia=referencia)

    mp_public_key = settings.MERCADOPAGO_PUBLIC_KEY

    email_pagador = "cliente@exemplo.com"
    if pedido.comprador and pedido.comprador.usuario and pedido.comprador.usuario.email:
        email_pagador = pedido.comprador.usuario.email

    return render(request, "pagamento_cartao.html", {
        "pedido": pedido,
        "pedidos": pedidos_lista,
        "referencia": referencia,
        "total": total,
        "forma_pagamento": pedido.forma_pagamento,
        "tipo_cartao": pedido.tipo_cartao,
        "mp_public_key": mp_public_key,
        "email_pagador": email_pagador,
    })
@login_required
def status_pagamento(request, referencia):
    pedidos = Pedido.objects.filter(referencia_pagamento=referencia).order_by("id")

    if not pedidos.exists():
        return JsonResponse({"ok": False, "erro": "Pedido não encontrado"}, status=404)

    pedido = pedidos.first()

    if pedido.status_pagamento == "pago":
        return JsonResponse({
            "ok": True,
            "status": "pago",
            "status_pagamento": "pago",
            "status_pedido": pedido.status,
            "referencia": referencia,
            "pago": True,
        })

    if pedido.mp_payment_id:
        try:
            response = requests.get(
                f"https://api.mercadopago.com/v1/payments/{pedido.mp_payment_id}",
                headers={
                    "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"
                },
                timeout=20
            )

            if response.status_code == 200:
                pagamento = response.json()
                status_mp = pagamento.get("status")

                if status_mp == "approved":
                    confirmar_pagamento_por_referencia(referencia)
                    pedido.refresh_from_db()

                elif status_mp in ["pending", "in_process"]:
                    Pedido.objects.filter(referencia_pagamento=referencia).update(
                        status_pagamento="confirmação"
                    )
                    pedido.refresh_from_db()

                elif status_mp in ["rejected", "cancelled"]:
                    Pedido.objects.filter(referencia_pagamento=referencia).update(
                        status_pagamento="recusado"
                    )
                    pedido.refresh_from_db()

        except Exception:
            pass

    return JsonResponse({
        "ok": True,
        "status": pedido.status_pagamento,
        "status_pagamento": pedido.status_pagamento,
        "status_pedido": pedido.status,
        "referencia": referencia,
        "pago": pedido.status_pagamento == "pago",
    })


@login_required
def pagamento_sucesso(request, referencia):
    pedidos = Pedido.objects.filter(referencia_pagamento=referencia).order_by("id")

    if not pedidos.exists():
        return redirect("home")

    pedido = pedidos.first()

    return render(request, "pagamento_sucesso.html", {
        "pedido": pedido,
        "referencia": referencia,
    })


def compra_sucesso(request):
    slug = request.session.get("ultima_loja_slug")
    loja = None
    if slug:
        loja = Loja.objects.filter(slug=slug).first()

    comprador_logado = get_comprador_logado(request, loja) if loja else None
    forma_pagamento = request.session.get("ultimo_pagamento")
    tipo_cartao = request.session.get("ultimo_tipo_cartao")
    total = request.session.get("ultimo_total")
    referencia_pagamento = request.session.get("ultima_referencia_pagamento")

    pedido_pix = None
    if referencia_pagamento:
        pedido_pix = Pedido.objects.filter(
            referencia_pagamento=referencia_pagamento,
            forma_pagamento="pix",
        ).first()

    return render(request, "compra_sucesso.html", {
        "loja": loja,
        "comprador_logado": comprador_logado,
        "forma_pagamento": forma_pagamento,
        "tipo_cartao": tipo_cartao,
        "total": total,
        "referencia_pagamento": referencia_pagamento,
        "pedido_pix": pedido_pix,
        "total_itens_carrinho": total_itens_carrinho(request),
    })


@login_required
def painel_loja(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    loja.verificar_licenca()

    produtos = Produto.objects.filter(loja=loja)
    pedidos_qs = Pedido.objects.filter(loja=loja)

    faturamento_total = sum(
        p.valor_total for p in pedidos_qs if p.status_pagamento == "pago"
    )

    pedidos_pendentes = pedidos_qs.filter(status="pendente").count()

    categorias_resumo = (
        Categoria.objects
        .filter(loja=loja)
        .annotate(total_produtos=Count("produto"))
        .order_by("nome")
    )

    total_estoque = produtos.aggregate(total=Sum("estoque"))["total"] or 0
    total_clientes = Comprador.objects.filter(loja=loja).count()

    hoje = timezone.localdate()
    pedidos_hoje = pedidos_qs.filter(data__date=hoje).count()

    inicio_periodo = hoje.replace(day=1) - timedelta(days=365)

    movimento_mensal_qs = (
        pedidos_qs
        .filter(data__date__gte=inicio_periodo)
        .annotate(mes=TruncMonth("data"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )

    mapa_meses = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
        5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
        9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }

    movimento_mensal = []
    for item in movimento_mensal_qs:
        mes_data = item["mes"]
        movimento_mensal.append({
            "mes": mapa_meses[mes_data.month],
            "total": item["total"],
        })

    if len(movimento_mensal) > 12:
        movimento_mensal = movimento_mensal[-12:]

    maior_total = max([item["total"] for item in movimento_mensal], default=1)

    for item in movimento_mensal:
        percentual = int((item["total"] / maior_total) * 100) if maior_total > 0 else 0
        item["altura"] = max(percentual, 12)

    valor_total_estoque = sum(
        (produto.custo or 0) * (produto.estoque or 0)
        for produto in produtos
    )

    config_frete = ConfigFrete.objects.filter(loja=loja).first()
    mp_connected = config_frete.mp_connected if config_frete else False

    return render(request, "painel_loja.html", {
        "loja": loja,
        "total_produtos": produtos.count(),
        "produtos_ativos": produtos.filter(ativo=True).count(),
        "total_pedidos": pedidos_qs.count(),
        "pedidos_hoje": pedidos_hoje,
        "pedidos_pendentes": pedidos_pendentes,
        "faturamento_total": faturamento_total,
        "categorias_resumo": categorias_resumo,
        "total_estoque": total_estoque,
        "valor_total_estoque": valor_total_estoque,
        "movimento_mensal": movimento_mensal,
        "total_clientes": total_clientes,
        "licenca_bloqueada": loja_com_licenca_bloqueada(loja),
        "mp_connected": mp_connected,
    })
@login_required
def financeiro_loja(request):
    loja = get_loja_do_dono(request)

    if not loja:
        return redirect("login_loja")

    loja.verificar_licenca()

    historico_pagamentos = PagamentoLicenca.objects.filter(
        loja=loja
    ).order_by("-data_criacao")

    pagamento_pendente = historico_pagamentos.filter(
        status="pendente"
    ).first()

    return render(request, "financeiro_loja.html", {
        "loja": loja,
        "licenca_bloqueada": loja_com_licenca_bloqueada(loja),
        "historico_pagamentos": historico_pagamentos,
        "pagamento_pendente": pagamento_pendente,
    })
@login_required
def renovar_licenca_manual(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    if request.method == "POST":
        loja.renovar_licenca(dias=30)

    return redirect("financeiro_loja")

@login_required
def gerar_pix_licenca(request):
    loja = get_loja_do_dono(request)

    pagamento_existente = PagamentoLicenca.objects.filter(
        loja=loja,
        tipo_pagamento="pix",
        status__in=["criado", "pendente"]
    ).order_by("-data_criacao").first()

    if pagamento_existente and pagamento_existente.qr_code:
        return JsonResponse({
            "ok": True,
            "pagamento_id": pagamento_existente.id,
            "qr_code": pagamento_existente.qr_code,
            "qr_code_base64": pagamento_existente.qr_code_base64,
        })

    external_reference = _criar_external_reference(loja, "pix")

    pagamento = PagamentoLicenca.objects.create(
        loja=loja,
        valor=loja.valor_licenca,
        tipo_pagamento="pix",
        external_reference=external_reference,
        status="criado",
        plano_nome="Plano padrão"
        )

    payload = {
        "transaction_amount": float(loja.valor_licenca),
        "description": f"Licença da loja {loja.nome}",
        "payment_method_id": "pix",
        "external_reference": external_reference,
        "payer": {
            "email": loja.email_comercial or request.user.email
        }
    }

    response = requests.post(
        "https://api.mercadopago.com/v1/payments",
        headers=_headers_mp(),
        json=payload,
    )

    data = response.json()

    tx = data.get("point_of_interaction", {}).get("transaction_data", {})

    pagamento.mp_payment_id = str(data.get("id", ""))
    pagamento.qr_code = tx.get("qr_code")
    pagamento.qr_code_base64 = tx.get("qr_code_base64")
    pagamento.status = "pendente"
    pagamento.save()

    return JsonResponse({
        "ok": True,
        "pagamento_id": pagamento.id,
        "qr_code": pagamento.qr_code,
        "qr_code_base64": pagamento.qr_code_base64,
    })
@login_required
def gerar_checkout_licenca(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return JsonResponse({"ok": False, "erro": "Loja não encontrada."}, status=404)

    token = _get_mp_token()
    if not token:
        return JsonResponse({
            "ok": False,
            "erro": "O token MERCADOPAGO_ACCESS_TOKEN não está configurado."
        }, status=400)

    try:
        valor = float(loja.valor_licenca or 0)
    except Exception:
        return JsonResponse({
            "ok": False,
            "erro": "Valor da licença inválido."
        }, status=400)

    if valor <= 0:
        return JsonResponse({
            "ok": False,
            "erro": "O valor da licença precisa ser maior que zero."
        }, status=400)

    external_reference = _criar_external_reference(loja, "checkout")
    notification_url = request.build_absolute_uri(reverse("webhook_mercadopago_licenca"))
    retorno_url = request.build_absolute_uri(reverse("financeiro_loja"))

    pagamento = PagamentoLicenca.objects.create(
    loja=loja,
    valor=loja.valor_licenca,
    tipo_pagamento="checkout",
    external_reference=external_reference,
    status="criado",
   plano_nome="Plano padrão"
   )

    payload = {
        "items": [
            {
                "title": f"Licença da loja {loja.nome}",
                "quantity": 1,
                "unit_price": valor,
                "currency_id": "BRL",
            }
        ],
        "external_reference": external_reference,
        "notification_url": notification_url,
        "back_urls": {
            "success": retorno_url,
            "failure": retorno_url,
            "pending": retorno_url,
        },
        "auto_return": "approved",
        "payer": {
            "email": loja.email_comercial or request.user.email or "cliente@exemplo.com"
        }
    }

    try:
        response = requests.post(
            "https://api.mercadopago.com/checkout/preferences",
            headers=_headers_mp(idempotency_key=f"licenca-checkout-{external_reference}"),
            json=payload,
            timeout=30,
        )
    except requests.Timeout:
        return JsonResponse({
            "ok": False,
            "erro": "Tempo esgotado ao gerar o checkout da licença."
        }, status=504)
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "erro": str(e)
        }, status=500)

    try:
        resposta = response.json()
    except Exception:
        resposta = {"raw": response.text}

    if response.status_code not in [200, 201]:
        return JsonResponse({
            "ok": False,
            "erro": "Não foi possível gerar o checkout da licença.",
            "resposta_mp": resposta,
        }, status=400)

    pagamento.mp_preference_id = resposta.get("id")
    pagamento.mp_init_point = resposta.get("init_point") or resposta.get("sandbox_init_point")
    pagamento.status = "pendente"
    pagamento.save()

    if not pagamento.mp_init_point:
        return JsonResponse({
            "ok": False,
            "erro": "O Mercado Pago não retornou o link de pagamento."
        }, status=400)

    return JsonResponse({
        "ok": True,
        "pagamento_id": pagamento.id,
        "checkout_url": pagamento.mp_init_point,
    })
@login_required
def lista_produtos_painel(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    if loja_com_licenca_bloqueada(loja):
        return redirect("painel_loja")

    produtos = Produto.objects.filter(loja=loja).order_by("-id")

    return render(request, "lista_produtos_painel.html", {
        "loja": loja,
        "produtos": produtos,
    })


@login_required
def cadastrar_produto(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    if loja_com_licenca_bloqueada(loja):
        return redirect("painel_loja")

    if request.method == "POST":
        form = ProdutoForm(request.POST, request.FILES)
        form.fields["categoria"].queryset = Categoria.objects.filter(loja=loja)

        if form.is_valid():
            try:
                produto = form.save(commit=False)
                produto.loja = loja
                produto.save()

                if produto.produto_novo or produto.em_destaque or produto.percentual_promocao > 0:
                    enviar_notificacao_produto(produto)

                imagens_extras = request.FILES.getlist("imagens_extras")
                for indice, imagem in enumerate(imagens_extras):
                    ProdutoImagem.objects.create(
                        produto=produto,
                        imagem=imagem,
                        ordem=indice
                    )

                if produto.estoque > 0:
                    MovimentacaoEstoque.objects.create(
                        loja=loja,
                        produto=produto,
                        tipo="entrada",
                        quantidade=produto.estoque,
                        motivo="Cadastro inicial",
                    )

                return redirect("lista_produtos_painel")

            except Exception as e:
                print("ERRO AO SALVAR PRODUTO:", str(e))

        else:
            print("ERROS FORM CADASTRO:", form.errors.as_json())
            print("POST:", request.POST)
            print("FILES:", request.FILES)

    else:
        form = ProdutoForm()
        form.fields["categoria"].queryset = Categoria.objects.filter(loja=loja)

    return render(request, "cadastrar_produto.html", {
        "form": form,
        "loja": loja,
    })
@login_required
def editar_produto(request, produto_id):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    produto = get_object_or_404(Produto, id=produto_id, loja=loja)
    estoque_anterior = produto.estoque
    categorias = Categoria.objects.filter(loja=loja).order_by("nome")

    if request.method == "POST":
        form = ProdutoForm(request.POST, request.FILES, instance=produto)
        form.fields["categoria"].queryset = categorias

        if form.is_valid():
            produto_editado = form.save(commit=False)
            novo_estoque = produto_editado.estoque
            diferenca = novo_estoque - estoque_anterior

            produto_editado.save()

            imagens_extras = request.FILES.getlist("imagens_extras")
            ordem_inicial = produto_editado.imagens_extras.count()

            for indice, imagem in enumerate(imagens_extras, start=ordem_inicial):
                ProdutoImagem.objects.create(
                    produto=produto_editado,
                    imagem=imagem,
                    ordem=indice
                )

            if diferenca > 0:
                MovimentacaoEstoque.objects.create(
                    loja=loja,
                    produto=produto_editado,
                    tipo="entrada",
                    quantidade=diferenca,
                    motivo="Ajuste manual",
                )
            elif diferenca < 0:
                MovimentacaoEstoque.objects.create(
                    loja=loja,
                    produto=produto_editado,
                    tipo="saida",
                    quantidade=abs(diferenca),
                    motivo="Ajuste manual",
                )

            return redirect("lista_produtos_painel")
        else:
            print("ERROS FORM EDITAR:", form.errors)
            print("FILES RECEBIDOS:", request.FILES)
    else:
        form = ProdutoForm(instance=produto)
        form.fields["categoria"].queryset = categorias

    return render(request, "editar_produto.html", {
        "form": form,
        "loja": loja,
        "produto": produto,
        "categorias": categorias,
        "imagens_extras": produto.imagens_extras.all(),
    })
def minha_loja(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    loja.verificar_licenca()

    return render(request, "minha_loja.html", {
        "loja": loja,
        "licenca_bloqueada": loja_com_licenca_bloqueada(loja),
    })


@login_required
def editar_dados_loja(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    if request.method == "POST":
        form = LojaDadosForm(request.POST, request.FILES, instance=loja)
        if form.is_valid():
            form.save()
            return redirect("minha_loja")
        else:
            print("ERROS FORM LOJA:", form.errors.as_json())
            print("POST:", request.POST)
            print("FILES:", request.FILES)
    else:
        form = LojaDadosForm(instance=loja)

    return render(request, "editar_dados_loja.html", {
        "loja": loja,
        "form": form,
        "licenca_bloqueada": loja_com_licenca_bloqueada(loja),
    })
@login_required
def editar_vitrine(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    if request.method == "POST":
        form = LojaVitrineForm(request.POST, request.FILES, instance=loja)
        if form.is_valid():
            form.save()
            return redirect("minha_loja")
    else:
        form = LojaVitrineForm(instance=loja)

    return render(request, "editar_vitrine.html", {
        "loja": loja,
        "form": form,
        "licenca_bloqueada": loja_com_licenca_bloqueada(loja),
    })


@login_required
def resetar_vitrine(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    if not plano_permite_vitrine(loja):
        return HttpResponse(
            "Seu plano atual não permite resetar a vitrine da loja.",
            status=403
        )

    if request.method == "POST":
        loja.banner_titulo = "+ PRODUTOS NA SUA LOJA"
        loja.banner_subtitulo = "Compre com praticidade e encontre tudo em um só lugar."
        loja.banner_botao_texto = "Comprar agora"
        loja.banner_botao_link = "#produtos"
        loja.banner_cor_inicio = "#16a34a"
        loja.banner_cor_fim = "#2563eb"
        loja.texto_busca = "O que você procura?"
        loja.save()

    return redirect("editar_vitrine")


@login_required
def nova_categoria(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.loja = loja
            categoria.save()
            return redirect("categorias")
    else:
        form = CategoriaForm()

    return render(request, "nova_categoria.html", {
        "loja": loja,
        "form": form,
    })


@login_required
def pedidos(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    pedidos_lista = Pedido.objects.filter(loja=loja).order_by("-data")
    pedidos_lista = aplicar_filtro_data(pedidos_lista, data_inicio, data_fim)

    return render(request, "pedidos.html", {
        "loja": loja,
        "pedidos": pedidos_lista,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    })


@login_required
def detalhe_pedido(request, pedido_id):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    pedido = get_object_or_404(Pedido, id=pedido_id, loja=loja)

    return render(request, "detalhe_pedido.html", {
        "pedido": pedido,
        "loja": loja,
    })


@login_required
def alterar_status_pedido(request, pedido_id, novo_status):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    pedido = get_object_or_404(Pedido, id=pedido_id, loja=loja)

    status_validos = [
        "pendente",
        "aguardando_envio",
        "enviado",
        "saiu_entrega",
        "entregue",
        "cancelado",
    ]

    if novo_status not in status_validos:
        return redirect("pedidos")

    pedido.status = novo_status
    pedido.save()

    enviar_email_status_pedido(pedido)

    return redirect("pedidos")


@login_required
def clientes(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    pedidos_lista = Pedido.objects.filter(loja=loja)

    nomes_unicos = []
    for pedido in pedidos_lista:
        if pedido.nome_cliente not in nomes_unicos:
            nomes_unicos.append(pedido.nome_cliente)

    return render(request, "clientes.html", {
        "loja": loja,
        "clientes": nomes_unicos,
    })


@login_required
def compradores_painel(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    compradores = Comprador.objects.filter(loja=loja).select_related("usuario").order_by("-id")

    return render(request, "compradores_painel.html", {
        "loja": loja,
        "compradores": compradores,
    })


@login_required
def alterar_status_comprador(request, comprador_id):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    comprador = get_object_or_404(Comprador, id=comprador_id, loja=loja)
    comprador.ativo = not comprador.ativo
    comprador.save()

    return redirect("compradores_painel")


@login_required
def vendas(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    pedidos_ok = Pedido.objects.filter(
        loja=loja,
        status_pagamento="pago",
    ).order_by("-data")

    pedidos_ok = aplicar_filtro_data(pedidos_ok, data_inicio, data_fim)

    faturamento_total = sum(p.valor_total for p in pedidos_ok)

    return render(request, "vendas.html", {
        "loja": loja,
        "pedidos": pedidos_ok,
        "faturamento_total": faturamento_total,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    })


@login_required
def entradas_saidas(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    movimentacoes = MovimentacaoEstoque.objects.filter(loja=loja).order_by("-data")
    movimentacoes = aplicar_filtro_data(movimentacoes, data_inicio, data_fim)

    entradas_total = sum(m.quantidade for m in movimentacoes if m.tipo == "entrada")
    saidas_total = sum(m.quantidade for m in movimentacoes if m.tipo == "saida")
    saldo = entradas_total - saidas_total

    return render(request, "entradas_saidas.html", {
        "loja": loja,
        "movimentacoes": movimentacoes,
        "entradas_total": entradas_total,
        "saidas_total": saidas_total,
        "saldo": saldo,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    })


@login_required
def relatorios(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    total_produtos = Produto.objects.filter(loja=loja).count()
    total_pedidos = Pedido.objects.filter(loja=loja).count()

    faturamento_total = Pedido.objects.filter(
        loja=loja,
        status_pagamento="pago"
    ).aggregate(total=Sum("valor_total"))["total"] or 0

    return render(request, "relatorios.html", {
        "loja": loja,
        "total_produtos": total_produtos,
        "total_pedidos": total_pedidos,
        "faturamento_total": faturamento_total,
    })


@login_required
def exportar_excel(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    if not plano_permite_exportar_excel(loja):
        return HttpResponse(
            "Seu plano atual não permite exportação para Excel.",
            status=403
        )

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    pedidos_lista = Pedido.objects.filter(loja=loja).order_by("-data")
    pedidos_lista = aplicar_filtro_data(pedidos_lista, data_inicio, data_fim)

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Relatorio"

    sheet.append([
        "ID Pedido",
        "Cliente",
        "Produto",
        "Categoria",
        "Preco Unitario",
        "Quantidade",
        "Frete",
        "Total",
        "Pagamento",
        "Status Pagamento",
        "Status Pedido",
        "Data",
    ])

    for pedido in pedidos_lista:
        categoria_nome = ""
        if pedido.produto.categoria:
            categoria_nome = pedido.produto.categoria.nome

        sheet.append([
            pedido.id,
            pedido.nome_cliente,
            pedido.produto.nome,
            categoria_nome,
            float(pedido.produto.preco),
            pedido.quantidade,
            float(pedido.valor_frete),
            float(pedido.valor_total),
            pedido.get_forma_pagamento_display(),
            pedido.get_status_pagamento_display(),
            pedido.get_status_display(),
            pedido.data.strftime("%d/%m/%Y %H:%M"),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=relatorio_loja.xlsx"

    workbook.save(response)
    return response


@login_required
def frete_entrega(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    config, _ = ConfigFrete.objects.get_or_create(loja=loja)
    faixas = FaixaFrete.objects.filter(loja=loja).order_by("km_inicial")

    return render(request, "frete_entrega.html", {
        "loja": loja,
        "config": config,
        "faixas": faixas,
    })


@login_required
def editar_config_frete(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    config, _ = ConfigFrete.objects.get_or_create(loja=loja)

    if request.method == "POST":
        form = ConfigFreteForm(request.POST, instance=config)
        if form.is_valid():
            config_editada = form.save(commit=False)
            config_editada.loja = loja
            config_editada.save()
            return redirect("frete_entrega")
    else:
        form = ConfigFreteForm(instance=config)

    return render(request, "editar_config_frete.html", {
        "loja": loja,
        "form": form,
    })


@login_required
def excluir_faixa_frete(request, faixa_id):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    faixa = get_object_or_404(FaixaFrete, id=faixa_id, loja=loja)
    faixa.delete()

    return redirect("frete_entrega")


@login_required
def nova_faixa_frete(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    if request.method == "POST":
        form = FaixaFreteForm(request.POST)
        if form.is_valid():
            faixa = form.save(commit=False)
            faixa.loja = loja
            faixa.save()
            return redirect("frete_entrega")
        else:
            print(form.errors)
    else:
        form = FaixaFreteForm()

    return render(request, "nova_faixa_frete.html", {
        "loja": loja,
        "form": form,
    })


@login_required
def editar_faixa_frete(request, faixa_id):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    faixa = get_object_or_404(FaixaFrete, id=faixa_id, loja=loja)

    if request.method == "POST":
        form = FaixaFreteForm(request.POST, instance=faixa)
        if form.is_valid():
            faixa_editada = form.save(commit=False)
            faixa_editada.loja = loja
            faixa_editada.save()
            return redirect("frete_entrega")
        else:
            print(form.errors)
    else:
        form = FaixaFreteForm(instance=faixa)

    return render(request, "editar_faixa_frete.html", {
        "loja": loja,
        "form": form,
        "faixa": faixa,
    })


@login_required
def pagamentos_painel(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    config, _ = ConfigFrete.objects.get_or_create(loja=loja)
    loja.verificar_licenca()

    return render(request, "pagamentos_painel.html", {
        "loja": loja,
        "config": config,
        "mp_public_key_plataforma": settings.MERCADOPAGO_PUBLIC_KEY,
        "licenca_bloqueada": loja_com_licenca_bloqueada(loja),
    })

@login_required
def conectar_mercadopago(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    request.session["oauth_loja_id"] = loja.id

    params = {
        "client_id": settings.MERCADOPAGO_CLIENT_ID,
        "response_type": "code",
        "platform_id": "mp",
        "redirect_uri": settings.MERCADOPAGO_REDIRECT_URI,
    }

    url = "https://auth.mercadopago.com.br/authorization?" + urllib.parse.urlencode(params)
    return redirect(url)


@login_required
def callback_mercadopago(request):
    loja_id = request.session.get("oauth_loja_id")
    if not loja_id:
        return redirect("pagamentos_painel")

    loja = get_object_or_404(Loja, id=loja_id, dono=request.user)
    config, _ = ConfigFrete.objects.get_or_create(loja=loja)

    code = request.GET.get("code")
    if not code:
        return redirect("pagamentos_painel")

    payload = urllib.parse.urlencode({
        "client_id": settings.MERCADOPAGO_CLIENT_ID,
        "client_secret": settings.MERCADOPAGO_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.MERCADOPAGO_REDIRECT_URI,
        "state": str(loja.id),
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.mercadopago.com/oauth/token",
        data=payload,
        headers={
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception:
        return redirect("pagamentos_painel")

    config.mp_connected = True
    config.mp_user_id = str(body.get("user_id", ""))
    config.mp_access_token = body.get("access_token", "")
    config.mp_refresh_token = body.get("refresh_token", "")
    config.mp_public_key = body.get("public_key", "")
    config.mp_token_expires_in = body.get("expires_in")
    config.save()

    return redirect("pagamentos_painel")


@csrf_exempt
def webhook_mercadopago(request):
    print("=== WEBHOOK RECEBIDO ===")
    print("METHOD:", request.method)
    print("GET:", request.GET.dict())
    print("BODY RAW:", request.body.decode("utf-8", errors="ignore"))

    try:
        payment_id = request.GET.get("data.id") or request.GET.get("id")

        if not payment_id:
            try:
                data = json.loads(request.body.decode("utf-8") or "{}")
                payment_id = data.get("data", {}).get("id") or data.get("id")
            except Exception:
                payment_id = None

        print("PAYMENT_ID:", payment_id)

        if not payment_id:
            return JsonResponse({"ok": True, "msg": "sem payment_id"}, status=200)

        response = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers={"Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"},
            timeout=20
        )

        print("WEBHOOK CONSULTA STATUS:", response.status_code)
        print("WEBHOOK CONSULTA RAW:", response.text)

        if response.status_code != 200:
            return JsonResponse({"ok": True, "msg": "pagamento nao encontrado"}, status=200)

        pagamento = response.json()
        status = pagamento.get("status")
        referencia = pagamento.get("external_reference")

        print("STATUS PAGAMENTO:", status)
        print("REFERENCIA PAGAMENTO:", referencia)

        if referencia:
            if status == "approved":
                confirmar_pagamento_por_referencia(referencia)
                print("PAGAMENTO CONFIRMADO COM SUCESSO")

            elif status in ["pending", "in_process"]:
                Pedido.objects.filter(referencia_pagamento=referencia).update(
                    status_pagamento="confirmação"
                )

            elif status in ["rejected", "cancelled"]:
                Pedido.objects.filter(referencia_pagamento=referencia).update(
                    status_pagamento="recusado"
                )

        return JsonResponse({"ok": True}, status=200)

    except Exception as e:
        print("ERRO WEBHOOK:", str(e))
        return JsonResponse({"ok": True, "erro": str(e)}, status=200)


@csrf_exempt
def webhook_mercadopago_licenca(request):
    if request.method not in ["POST", "GET"]:
        return JsonResponse({"ok": False, "msg": "Método inválido"}, status=405)

    try:
        payment_id = request.GET.get("data.id") or request.GET.get("id")

        if not payment_id:
            try:
                body = json.loads(request.body.decode("utf-8"))
                payment_id = body.get("data", {}).get("id") or body.get("id")
            except Exception:
                payment_id = None

        if not payment_id:
            return JsonResponse({"ok": True, "msg": "sem payment_id"})

        response = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers={
                "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"
            },
            timeout=20
        )

        if response.status_code != 200:
            return JsonResponse({"ok": False, "msg": "falha ao consultar pagamento"}, status=400)

        pagamento = response.json()
        status_mp = pagamento.get("status")
        external_reference = pagamento.get("external_reference", "")

        if not external_reference.startswith("LICENCA_LOJA_"):
            return JsonResponse({"ok": True, "msg": "pagamento não é de licença"})

        loja_id = external_reference.replace("LICENCA_LOJA_", "").strip()

        try:
            loja = Loja.objects.get(id=loja_id)
        except Loja.DoesNotExist:
            return JsonResponse({"ok": False, "msg": "loja não encontrada"}, status=404)

        if status_mp == "approved":
            plano = (loja.plano_licenca or "").strip().lower()

            if "anual" in plano:
                ativar_ou_renovar_licenca(loja, dias=365)
            else:
                ativar_ou_renovar_licenca(loja, dias=30)

            return JsonResponse({"ok": True, "msg": "licença ativada"})

        return JsonResponse({"ok": True, "msg": f"status recebido: {status_mp}"})

    except Exception as e:
        return JsonResponse({"ok": False, "erro": str(e)}, status=500)


@login_required
def simular_pagamento_aprovado(request, referencia):
    confirmar_pagamento_por_referencia(referencia)
    return redirect("painel_loja")


@csrf_exempt
def criar_pagamento_cartao(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "erro": "Método inválido."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        referencia = data.get("referencia")
        payload_front = data.get("payload", {})
        transaction_amount = float(data.get("transaction_amount") or 0)

        if not referencia:
            return JsonResponse({"ok": False, "erro": "Referência não informada."}, status=400)

        pedidos_lista = Pedido.objects.filter(
            referencia_pagamento=referencia
        ).order_by("id")

        if not pedidos_lista.exists():
            return JsonResponse({"ok": False, "erro": "Pedido não encontrado."}, status=404)

        pedido_base = pedidos_lista.first()
        total = float(sum((p.valor_total for p in pedidos_lista), Decimal("0.00")))

        if pedido_base.status_pagamento == "pago":
            return JsonResponse({
                "ok": True,
                "ja_pago": True,
                "redirect": f"/pagamento/{referencia}/sucesso/"
            })

        if not transaction_amount:
            transaction_amount = total

        payload_mp = {
            "transaction_amount": transaction_amount,
            "token": payload_front.get("token"),
            "description": f"Pedido {referencia}",
            "installments": int(payload_front.get("installments") or 1),
            "payment_method_id": payload_front.get("paymentMethodId"),
            "external_reference": referencia,
            "notification_url": settings.MERCADOPAGO_WEBHOOK_URL,
            "payer": {
                "email": payload_front.get("cardholderEmail"),
                "first_name": payload_front.get("cardholderName") or "Cliente",
                "identification": {
                    "type": payload_front.get("identificationType"),
                    "number": payload_front.get("identificationNumber")
                }
            }
        }

        response = requests.post(
            "https://api.mercadopago.com/v1/payments",
            headers={
                "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json=payload_mp,
            timeout=30
        )

        resposta = response.json()

        if response.status_code not in [200, 201]:
            return JsonResponse({"ok": False, "erro": resposta}, status=400)

        status = resposta.get("status", "")

        if status == "approved":
            Pedido.objects.filter(referencia_pagamento=referencia).update(
                status_pagamento="pago",
                status="aguardando_envio"
            )

            confirmar_pagamento_por_referencia(referencia)

            return JsonResponse({
                "ok": True,
                "redirect": f"/pagamento/{referencia}/sucesso/"
            })

        return JsonResponse({"ok": True, "status": status})

    except Exception as e:
        return JsonResponse({"ok": False, "erro": str(e)}, status=500)

@csrf_exempt
def criar_pagamento_pix(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "erro": "Método inválido."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        referencia = data.get("referencia")

        if not referencia:
            return JsonResponse({"ok": False, "erro": "Referência não informada."}, status=400)

        pedidos_lista = Pedido.objects.filter(
            referencia_pagamento=referencia
        ).order_by("id")

        if not pedidos_lista.exists():
            return JsonResponse({"ok": False, "erro": "Pedido não encontrado."}, status=404)

        pedido_base = pedidos_lista.first()

        if pedido_base.status_pagamento == "pago":
            return JsonResponse({
                "ok": True,
                "ja_pago": True,
                "mensagem": "Pagamento já confirmado."
            })

        if pedido_base.mp_payment_id:
            try:
                response = requests.get(
                    f"https://api.mercadopago.com/v1/payments/{pedido_base.mp_payment_id}",
                    headers={
                        "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"
                    },
                    timeout=20
                )

                if response.status_code == 200:
                    pagamento = response.json()
                    status_mp = pagamento.get("status")

                    if status_mp == "approved":
                        confirmar_pagamento_por_referencia(referencia)
                        return JsonResponse({
                            "ok": True,
                            "ja_pago": True,
                            "mensagem": "Pagamento já confirmado."
                        })

                    elif status_mp in ["pending", "in_process"]:
                        Pedido.objects.filter(
                            referencia_pagamento=referencia
                        ).update(status_pagamento="confirmação")
                        pedido_base.status_pagamento = "em_analise"

                    elif status_mp in ["rejected", "cancelled"]:
                        Pedido.objects.filter(
                            referencia_pagamento=referencia
                        ).update(status_pagamento="recusado")
                        pedido_base.status_pagamento = "recusado"

            except Exception:
                pass

        if (
            pedido_base.mp_qr_code
            and pedido_base.mp_qr_code_base64
            and pedido_base.status_pagamento in ["aguardando", "em_analise"]
        ):
            return JsonResponse({
                "ok": True,
                "qr_code": pedido_base.mp_qr_code,
                "qr_code_base64": pedido_base.mp_qr_code_base64,
                "ticket_url": pedido_base.mp_ticket_url or "",
                "payment_id": pedido_base.mp_payment_id or "",
                "reutilizado": True,
            })

        total = float(sum((p.valor_total for p in pedidos_lista), Decimal("0.00")))

        email_pagador = "test_user_123@testuser.com"
        if (
            pedido_base.comprador
            and pedido_base.comprador.usuario
            and pedido_base.comprador.usuario.email
        ):
            email_pagador = pedido_base.comprador.usuario.email

        payload = {
            "transaction_amount": total,
            "description": f"Pedido {referencia}",
            "payment_method_id": "pix",
            "external_reference": referencia,
            "notification_url": settings.MERCADOPAGO_WEBHOOK_URL,
            "payer": {
                "email": email_pagador
            }
        }

        response = requests.post(
            "https://api.mercadopago.com/v1/payments",
            headers={
                "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Idempotency-Key": f"pix-{referencia}",
            },
            json=payload,
            timeout=30,
        )

        try:
            resposta = response.json()
        except Exception:
            return JsonResponse({
                "ok": False,
                "erro": "Resposta inválida do Mercado Pago",
                "raw": response.text
            }, status=400)

        if response.status_code not in [200, 201]:
            return JsonResponse({
                "ok": False,
                "erro": "Erro ao criar pagamento",
                "resposta_mp": resposta
            }, status=400)

        point = resposta.get("point_of_interaction") or {}
        tx = point.get("transaction_data") or {}

        qr_code = tx.get("qr_code")
        qr_code_base64 = tx.get("qr_code_base64")
        ticket_url = tx.get("ticket_url", "")
        mp_payment_id = str(resposta.get("id", ""))

        if not qr_code or not qr_code_base64:
            return JsonResponse({
                "ok": False,
                "erro": "MP não retornou QR Code",
                "resposta_mp": resposta
            }, status=400)

        Pedido.objects.filter(referencia_pagamento=referencia).update(
            mp_payment_id=mp_payment_id,
            mp_qr_code=qr_code,
            mp_qr_code_base64=qr_code_base64,
            mp_ticket_url=ticket_url,
            status_pagamento="aguardando",
        )

        return JsonResponse({
            "ok": True,
            "qr_code": qr_code,
            "qr_code_base64": qr_code_base64,
            "ticket_url": ticket_url,
            "payment_id": mp_payment_id,
        })

    except Exception as e:
        return JsonResponse({"ok": False, "erro": str(e)}, status=500)


def login_loja(request):
    erro = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            loja = Loja.objects.filter(dono=user).first()

            if loja:
                login(request, user)
                loja.verificar_licenca()
                return redirect("painel_loja")

        erro = "Usuário ou senha inválidos."

    return render(request, "login_loja.html", {
        "erro": erro,
    })


@login_required
def categorias(request):
    loja = get_loja_do_dono(request)
    if not loja:
        return redirect("login_loja")

    bloqueio = bloquear_acesso_se_licenca_inativa(request, loja)
    if bloqueio:
        return bloqueio

    categorias_lista = Categoria.objects.filter(loja=loja)

    return render(request, "categorias.html", {
        "loja": loja,
        "categorias": categorias_lista,
    })
def recuperar_acesso_loja(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()

        if not email:
            messages.error(request, "Informe o e-mail.")
            return render(request, "recuperar_acesso_loja.html")

        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "E-mail não encontrado.")
            return render(request, "recuperar_acesso_loja.html")

        try:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            link = request.build_absolute_uri(
                reverse("redefinir_senha_loja", kwargs={"uidb64": uid, "token": token})
            )

            html_body = render_to_string(
                "email/recuperar_senha_loja.html",
                {
                    "user": user,
                    "link_recuperacao": link,
                },
            )

            enviar_email(
                email,
                "Recuperação de senha - NexaStore",
                html_body,
            )

            messages.success(request, "E-mail enviado com sucesso.")
            return redirect("login_loja")

        except Exception as e:
            print("ERRO RECUPERACAO:", e)
            messages.error(request, "Erro ao enviar e-mail.")
            return render(request, "recuperar_acesso_loja.html")

    return render(request, "recuperar_acesso_loja.html")

def recuperar_acesso_enviado(request):
    return render(request, "senha/enviado.html")


def redefinir_senha_loja(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if not user or not default_token_generator.check_token(user, token):
        return render(request, "senha/invalido.html")

    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            return redirect("redefinir_senha_concluida")
    else:
        form = SetPasswordForm(user)

    return render(request, "senha/redefinir.html", {"form": form})


def redefinir_senha_concluida(request):
    return render(request, "senha/concluido.html")

@login_required
def excluir_imagem_produto(request, imagem_id):
    imagem = get_object_or_404(ProdutoImagem, id=imagem_id)

    produto = imagem.produto
    loja = get_loja_do_dono(request)

    # segurança
    if produto.loja != loja:
        return redirect("painel_loja")

    imagem.delete()

    return redirect("editar_produto", produto_id=produto.id)

@login_required
def definir_imagem_principal(request, imagem_id):
    imagem_extra = get_object_or_404(ProdutoImagem, id=imagem_id)
    produto = imagem_extra.produto
    loja = get_loja_do_dono(request)

    if not loja or produto.loja != loja:
        return redirect("painel_loja")

    produto.imagem = imagem_extra.imagem
    produto.save()

    return redirect("editar_produto", produto_id=produto.id)

def ativar_conta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    loja_slug = None

    if user:
        comprador = Comprador.objects.filter(usuario=user).select_related("loja").first()
        if comprador and comprador.loja:
            loja_slug = comprador.loja.slug

    contexto = {
        "sucesso": False,
        "titulo": "Link inválido ou expirado",
        "mensagem": "Esse link de ativação não é mais válido. Solicite um novo cadastro ou tente novamente.",
        "loja_slug": loja_slug,
    }

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        contexto = {
            "sucesso": True,
            "titulo": "Conta ativada com sucesso",
            "mensagem": "Seu e-mail foi confirmado. Agora você já pode entrar na sua conta de comprador.",
            "loja_slug": loja_slug,
        }

    return render(request, "ativacao_conta_resultado.html", contexto)
@login_required
def remover_logo_ajax(request):
    if request.method != "POST":
        return JsonResponse({"status": "erro", "msg": "Método inválido"}, status=405)

    loja = Loja.objects.filter(dono=request.user).first()

    if not loja:
        return JsonResponse({"status": "erro", "msg": "Loja não encontrada"}, status=404)

    try:
        if loja.logo:
            loja.logo.delete(save=False)
        loja.logo = None
        loja.save(update_fields=["logo"])
        return JsonResponse({"status": "ok"})
    except Exception as e:
        print("ERRO remover_logo_ajax:", str(e))
        return JsonResponse({"status": "erro", "msg": str(e)}, status=500)

def status_licenca(request, pk):
    try:
        pagamento = PagamentoLicenca.objects.get(id=pk)

        return JsonResponse({
            "ok": True,
            "status": pagamento.status,
            "dias_restantes": pagamento.dias_restantes if hasattr(pagamento, 'dias_restantes') else None
        })
    except PagamentoLicenca.DoesNotExist:
        return JsonResponse({"ok": False}, status=404)

def recuperar_senha_comprador(request, slug):
    loja = get_object_or_404(Loja, slug=slug)

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()

        if not email:
            return render(request, "senha/recuperar_comprador.html", {
                "loja": loja,
                "erro": "Informe o e-mail."
            })

        user = User.objects.filter(email=email).first()

        if not user:
            return render(request, "senha/recuperar_comprador.html", {
                "loja": loja,
                "erro": "E-mail não encontrado."
            })

        comprador = Comprador.objects.filter(usuario=user, loja=loja).first()

        if not comprador:
            return render(request, "senha/recuperar_comprador.html", {
                "loja": loja,
                "erro": "Este e-mail não pertence a esta loja."
            })

        try:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            link = request.build_absolute_uri(
                reverse("redefinir_senha_comprador", kwargs={"uidb64": uid, "token": token})
            )

            html_body = f"""
            <h2>Recuperação de senha</h2>
            <p>Olá, {user.first_name}</p>
            <p>Clique abaixo para redefinir sua senha:</p>
            <a href="{link}">{link}</a>
            """

            enviar_email(
                user.email,
                f"Recuperação de senha - {loja.nome}",
                html_body
            )

            return redirect("recuperar_senha_comprador_enviado", slug=loja.slug)

        except Exception as e:
            print("ERRO RECUPERACAO COMPRADOR:", e)
            return render(request, "senha/recuperar_comprador.html", {
                "loja": loja,
                "erro": "Erro ao enviar e-mail."
            })

    return render(request, "senha/recuperar_comprador.html", {"loja": loja})


def recuperar_senha_comprador_enviado(request, slug):
    loja = get_object_or_404(Loja, slug=slug)
    return render(request, "senha/enviado_comprador.html", {"loja": loja})


def redefinir_senha_comprador(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if not user or not default_token_generator.check_token(user, token):
        return render(request, "senha/invalido.html")

    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            return redirect("redefinir_senha_comprador_concluida")
    else:
        form = SetPasswordForm(user)

    return render(request, "senha/redefinir.html", {"form": form})


def redefinir_senha_comprador_concluida(request):
    return render(request, "senha/concluido.html")
@login_required
def licenca_bloqueada(request):
    loja = get_loja_do_dono(request)

    if not loja:
        return redirect("login_loja")

    loja.verificar_licenca()

    if loja.status_licenca == "ativa" and loja.ativa:
        return redirect("painel_loja")

    return render(request, "licenca_bloqueada.html", {
        "loja": loja,
    })

def csrf_erro(request, reason=""):
    return render(request, "csrf_erro.html", status=403)