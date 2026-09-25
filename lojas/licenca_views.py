import json
from uuid import uuid4

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import Loja, PagamentoLicenca


def get_loja_do_dono(request):
    if not request.user.is_authenticated:
        return None

    loja = Loja.objects.filter(dono=request.user).first()

    if loja:
        loja.verificar_licenca()

    return loja


def loja_com_licenca_bloqueada(loja):
    if not loja:
        return True

    loja.verificar_licenca()

    if loja.status_licenca in ["pendente", "vencida"]:
        return True

    if not loja.ativa:
        return True

    return False


def _get_mp_token():
    token = getattr(settings, "MERCADOPAGO_ACCESS_TOKEN", "")
    return str(token).strip()


def _headers_mp(idempotency_key=None):
    token = _get_mp_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    if idempotency_key:
        headers["X-Idempotency-Key"] = idempotency_key

    return headers


def _criar_external_reference(loja, tipo):
    return f"LIC-{loja.id}-{tipo.upper()}-{uuid4().hex[:12].upper()}"


def _mapear_status_mp(status_mp):
    mapa = {
        "approved": "aprovado",
        "pending": "pendente",
        "in_process": "pendente",
        "rejected": "recusado",
        "cancelled": "cancelado",
        "expired": "expirado",
    }
    return mapa.get(status_mp, "pendente")


def _dias_licenca():
    return 30


def _montar_url_absoluta(caminho):
    base = str(getattr(settings, "PLATFORM_BASE_URL", "")).rstrip("/")
    return f"{base}{caminho}"


def _consultar_pagamento_mp(payment_id):
    token = _get_mp_token()

    if not token:
        return None, "Token não configurado"

    try:
        response = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
    except requests.Timeout:
        return None, "Tempo esgotado ao consultar pagamento."
    except Exception as e:
        return None, str(e)

    if response.status_code != 200:
        return None, response.text

    try:
        return response.json(), None
    except Exception:
        return None, "Resposta inválida do Mercado Pago."


def _consultar_assinatura_mp(preapproval_id):
    token = _get_mp_token()

    if not token:
        return None, "Token não configurado"

    try:
        response = requests.get(
            f"https://api.mercadopago.com/preapproval/{preapproval_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
    except requests.Timeout:
        return None, "Tempo esgotado ao consultar assinatura."
    except Exception as e:
        return None, str(e)

    if response.status_code != 200:
        return None, response.text

    try:
        return response.json(), None
    except Exception:
        return None, "Resposta inválida do Mercado Pago."


def _processar_pagamento_licenca_por_payment_id(payment_id):
    pagamento_mp, erro = _consultar_pagamento_mp(payment_id)

    if erro or not pagamento_mp:
        print("ERRO AO CONSULTAR PAGAMENTO MP:", erro)
        return False

    external_reference = pagamento_mp.get("external_reference")
    status_mp = pagamento_mp.get("status")

    if not external_reference:
        print("PAGAMENTO MP SEM EXTERNAL_REFERENCE")
        return False

    pagamento = PagamentoLicenca.objects.filter(
        external_reference=external_reference
    ).first()

    if not pagamento:
        print("PAGAMENTO LICENCA NÃO ENCONTRADO:", external_reference)
        return False

    status_antigo = pagamento.status
    novo_status = _mapear_status_mp(status_mp)

    pagamento.mp_payment_id = str(pagamento_mp.get("id", ""))
    pagamento.status = novo_status

    if novo_status == "aprovado" and status_antigo != "aprovado":
        pagamento.data_aprovacao = timezone.now()
        pagamento.save(update_fields=[
            "mp_payment_id",
            "status",
            "data_aprovacao",
            "data_atualizacao",
        ])
        pagamento.loja.renovar_licenca(dias=_dias_licenca())
        print("LICENÇA RENOVADA COM SUCESSO:", pagamento.loja.nome)
        return True

    pagamento.save(update_fields=[
        "mp_payment_id",
        "status",
        "data_atualizacao",
    ])

    return True


def _processar_assinatura_licenca_por_id(preapproval_id):
    assinatura_mp, erro = _consultar_assinatura_mp(preapproval_id)

    if erro or not assinatura_mp:
        print("ERRO AO CONSULTAR ASSINATURA MP:", erro)
        return False

    loja = Loja.objects.filter(mp_preapproval_id=preapproval_id).first()
    if not loja:
        print("ASSINATURA NÃO ENCONTRADA NO BANCO:", preapproval_id)
        return False

    status_mp = (assinatura_mp.get("status") or "").strip().lower()

    loja.mp_preapproval_status = status_mp
    loja.mp_preapproval_init_point = assinatura_mp.get("init_point") or loja.mp_preapproval_init_point

    if status_mp in ["authorized", "active"]:
        loja.cobranca_automatica_ativa = True
        loja.renovar_licenca(dias=_dias_licenca())
        loja.save(update_fields=[
            "mp_preapproval_status",
            "mp_preapproval_init_point",
            "cobranca_automatica_ativa",
            "atualizado_em",
        ])
        print("ASSINATURA ATIVA E LICENÇA RENOVADA:", loja.nome)
        return True

    if status_mp in ["paused", "cancelled"]:
        loja.cobranca_automatica_ativa = False
        loja.save(update_fields=[
            "mp_preapproval_status",
            "mp_preapproval_init_point",
            "cobranca_automatica_ativa",
            "atualizado_em",
        ])
        print("ASSINATURA INATIVA:", loja.nome)
        return True

    loja.save(update_fields=[
        "mp_preapproval_status",
        "mp_preapproval_init_point",
        "atualizado_em",
    ])
    return True


@login_required
def financeiro_loja(request):
    loja = get_loja_do_dono(request)

    if not loja:
        return redirect("login_loja")

    historico_pagamentos = PagamentoLicenca.objects.filter(
        loja=loja
    ).order_by("-data_criacao")

    pagamento_pendente = historico_pagamentos.filter(
        status="pendente"
    ).first()

    licenca_bloqueada = loja.status_licenca in ["vencida"]

    return render(request, "financeiro_loja.html", {
        "loja": loja,
        "historico_pagamentos": historico_pagamentos,
        "pagamento_pendente": pagamento_pendente,
        "licenca_bloqueada": licenca_bloqueada,
    })


@login_required
def renovar_licenca_manual(request):
    loja = get_loja_do_dono(request)

    if not loja:
        return redirect("login_loja")

    if request.method == "POST":
        loja.renovar_licenca(dias=_dias_licenca())

    return redirect("financeiro_loja")


@login_required
def gerar_pix_licenca(request):
    try:
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

        pagamento_existente = (
            PagamentoLicenca.objects
            .filter(loja=loja, tipo_pagamento="pix", status__in=["criado", "pendente"])
            .order_by("-data_criacao")
            .first()
        )

        if pagamento_existente:
            if pagamento_existente.mp_payment_id:
                _processar_pagamento_licenca_por_payment_id(pagamento_existente.mp_payment_id)
                pagamento_existente.refresh_from_db()

            if pagamento_existente.status == "aprovado":
                return JsonResponse({
                    "ok": True,
                    "ja_pago": True,
                    "mensagem": "A licença já foi paga e ativada."
                })

            if pagamento_existente.qr_code and pagamento_existente.qr_code_base64:
                return JsonResponse({
                    "ok": True,
                    "pagamento_id": pagamento_existente.id,
                    "status": pagamento_existente.status,
                    "qr_code": pagamento_existente.qr_code,
                    "qr_code_base64": pagamento_existente.qr_code_base64,
                    "ticket_url": pagamento_existente.ticket_url or "",
                    "reutilizado": True,
                })

        external_reference = _criar_external_reference(loja, "pix")
        notification_url = _montar_url_absoluta(reverse("webhook_mercadopago_licenca"))

        pagamento = PagamentoLicenca.objects.create(
            loja=loja,
            valor=loja.valor_licenca,
            tipo_pagamento="pix",
            external_reference=external_reference,
            status="criado",
            plano_nome="Plano padrão",
        )

        payload = {
            "transaction_amount": valor,
            "description": f"Licença da loja {loja.nome}",
            "payment_method_id": "pix",
            "external_reference": external_reference,
            "notification_url": notification_url,
            "payer": {
                "email": loja.email_comercial or request.user.email or "cliente@exemplo.com"
            }
        }

        response = requests.post(
            "https://api.mercadopago.com/v1/payments",
            headers=_headers_mp(idempotency_key=f"licenca-pix-{external_reference}"),
            json=payload,
            timeout=30,
        )

        try:
            data = response.json()
        except Exception:
            data = {"raw": response.text}

        if response.status_code not in [200, 201]:
            return JsonResponse({
                "ok": False,
                "erro": "Não foi possível gerar o Pix da licença.",
                "status_code_mp": response.status_code,
                "resposta_mp": data,
            }, status=400)

        tx = data.get("point_of_interaction", {}).get("transaction_data", {})

        qr_code = tx.get("qr_code")
        qr_code_base64 = tx.get("qr_code_base64")
        ticket_url = tx.get("ticket_url", "")
        mp_payment_id = str(data.get("id", ""))

        if not qr_code or not qr_code_base64:
            return JsonResponse({
                "ok": False,
                "erro": "O Mercado Pago não retornou os dados do QR Code.",
                "resposta_mp": data,
            }, status=400)

        pagamento.mp_payment_id = mp_payment_id
        pagamento.qr_code = qr_code
        pagamento.qr_code_base64 = qr_code_base64
        pagamento.ticket_url = ticket_url
        pagamento.status = "pendente"
        pagamento.save()

        return JsonResponse({
            "ok": True,
            "pagamento_id": pagamento.id,
            "status": pagamento.status,
            "qr_code": pagamento.qr_code,
            "qr_code_base64": pagamento.qr_code_base64,
            "ticket_url": pagamento.ticket_url or "",
            "payment_id": mp_payment_id,
        })

    except Exception as e:
        import traceback
        return JsonResponse({
            "ok": False,
            "erro": str(e),
            "traceback": traceback.format_exc(),
        }, status=500)


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
    notification_url = _montar_url_absoluta(reverse("webhook_mercadopago_licenca"))
    retorno_url = _montar_url_absoluta(reverse("financeiro_loja"))

    pagamento = PagamentoLicenca.objects.create(
        loja=loja,
        valor=loja.valor_licenca,
        tipo_pagamento="checkout",
        external_reference=external_reference,
        status="criado",
        plano_nome="Plano padrão",
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
        data = response.json()
    except Exception:
        data = {"raw": response.text}

    if response.status_code not in [200, 201]:
        return JsonResponse({
            "ok": False,
            "erro": "Não foi possível gerar o checkout da licença.",
            "resposta_mp": data,
        }, status=400)

    pagamento.mp_init_point = data.get("init_point") or data.get("sandbox_init_point")
    pagamento.mp_preference_id = data.get("id")
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
def criar_assinatura_automatica_licenca(request):
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

    if loja.mp_preapproval_id and loja.cobranca_automatica_ativa:
        return JsonResponse({
            "ok": True,
            "ja_existe": True,
            "mensagem": "A cobrança automática já está ativa para esta loja."
        })

    retorno_url = _montar_url_absoluta(reverse("financeiro_loja"))

    payload = {
        "reason": f"Assinatura da licença da loja {loja.nome}",
        "external_reference": f"ASSINATURA-LOJA-{loja.id}",
        "payer_email": loja.email_comercial or request.user.email or "cliente@exemplo.com",
        "back_url": retorno_url,
        "status": "pending",
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "transaction_amount": valor,
            "currency_id": "BRL",
        },
    }

    try:
        response = requests.post(
            "https://api.mercadopago.com/preapproval",
            headers=_headers_mp(idempotency_key=f"licenca-assinatura-{loja.id}"),
            json=payload,
            timeout=30,
        )
    except requests.Timeout:
        return JsonResponse({
            "ok": False,
            "erro": "Tempo esgotado ao gerar a assinatura automática."
        }, status=504)
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "erro": str(e)
        }, status=500)

    try:
        data = response.json()
    except Exception:
        data = {"raw": response.text}

    if response.status_code not in [200, 201]:
        return JsonResponse({
            "ok": False,
            "erro": "Não foi possível criar a assinatura automática.",
            "resposta_mp": data,
        }, status=400)

    loja.mp_preapproval_id = data.get("id")
    loja.mp_preapproval_status = data.get("status", "pending")
    loja.mp_preapproval_init_point = data.get("init_point") or ""
    loja.cobranca_automatica_ativa = loja.mp_preapproval_status in ["authorized", "active"]
    loja.save(update_fields=[
        "mp_preapproval_id",
        "mp_preapproval_status",
        "mp_preapproval_init_point",
        "cobranca_automatica_ativa",
        "atualizado_em",
    ])

    return JsonResponse({
        "ok": True,
        "assinatura_id": loja.mp_preapproval_id,
        "status": loja.mp_preapproval_status,
        "checkout_url": loja.mp_preapproval_init_point,
    })


@login_required
def status_assinatura_automatica_licenca(request):
    loja = get_loja_do_dono(request)

    if not loja:
        return JsonResponse({"ok": False, "erro": "Loja não encontrada."}, status=404)

    if loja.mp_preapproval_id:
        _processar_assinatura_licenca_por_id(loja.mp_preapproval_id)
        loja.refresh_from_db()

    return JsonResponse({
        "ok": True,
        "assinatura_id": loja.mp_preapproval_id or "",
        "status": loja.mp_preapproval_status or "",
        "ativa": bool(loja.cobranca_automatica_ativa),
        "status_licenca": loja.status_licenca,
        "dias_restantes": loja.dias_restantes_licenca,
    })


@login_required
def cancelar_assinatura_automatica_licenca(request):
    loja = get_loja_do_dono(request)

    if not loja:
        return JsonResponse({"ok": False, "erro": "Loja não encontrada."}, status=404)

    if not loja.mp_preapproval_id:
        return JsonResponse({"ok": False, "erro": "Nenhuma assinatura encontrada."}, status=404)

    token = _get_mp_token()
    if not token:
        return JsonResponse({
            "ok": False,
            "erro": "O token MERCADOPAGO_ACCESS_TOKEN não está configurado."
        }, status=400)

    payload = {"status": "cancelled"}

    try:
        response = requests.put(
            f"https://api.mercadopago.com/preapproval/{loja.mp_preapproval_id}",
            headers=_headers_mp(),
            json=payload,
            timeout=30,
        )
    except requests.Timeout:
        return JsonResponse({
            "ok": False,
            "erro": "Tempo esgotado ao cancelar a assinatura."
        }, status=504)
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "erro": str(e)
        }, status=500)

    try:
        data = response.json()
    except Exception:
        data = {"raw": response.text}

    if response.status_code not in [200, 201]:
        return JsonResponse({
            "ok": False,
            "erro": "Não foi possível cancelar a assinatura.",
            "resposta_mp": data,
        }, status=400)

    loja.mp_preapproval_status = "cancelled"
    loja.cobranca_automatica_ativa = False
    loja.save(update_fields=[
        "mp_preapproval_status",
        "cobranca_automatica_ativa",
        "atualizado_em",
    ])

    return JsonResponse({
        "ok": True,
        "mensagem": "Assinatura automática cancelada com sucesso."
    })


@login_required
def status_pagamento_licenca(request, pagamento_id):
    loja = get_loja_do_dono(request)

    if not loja:
        return JsonResponse({"ok": False, "erro": "Loja não encontrada."}, status=404)

    pagamento = get_object_or_404(
        PagamentoLicenca,
        id=pagamento_id,
        loja=loja
    )

    if pagamento.mp_payment_id:
        _processar_pagamento_licenca_por_payment_id(pagamento.mp_payment_id)
        pagamento.refresh_from_db()
        loja.refresh_from_db()
        loja.verificar_licenca()
        loja.refresh_from_db()

    return JsonResponse({
        "ok": True,
        "status": pagamento.status,
        "loja_ativa": loja.ativa,
        "status_licenca": loja.status_licenca,
        "dias_restantes": loja.dias_restantes_licenca,
        "vencimento": (
            loja.data_vencimento_licenca.strftime("%d/%m/%Y")
            if loja.data_vencimento_licenca else ""
        ),
    })


@csrf_exempt
def webhook_mercadopago_licenca(request):
    try:
        print("WEBHOOK LICENCA RECEBIDO")
        print("METHOD:", request.method)
        print("GET:", dict(request.GET))

        payment_id = request.GET.get("data.id") or request.GET.get("id")

        body_data = {}
        if request.body:
            try:
                body_data = json.loads(request.body.decode("utf-8"))
                print("BODY:", body_data)
            except Exception:
                print("BODY INVÁLIDO")

        preapproval_id = (
            body_data.get("data", {}).get("id")
            or body_data.get("id")
            or None
        )

        action = (body_data.get("action") or "").lower()

        if action.startswith("preapproval") and preapproval_id:
            print("PREAPPROVAL_ID CAPTURADO:", preapproval_id)
            _processar_assinatura_licenca_por_id(preapproval_id)
            return JsonResponse({"ok": True, "tipo": "assinatura"})

        if not payment_id:
            payment_id = (
                body_data.get("data", {}).get("id")
                or body_data.get("id")
                or (
                    body_data.get("resource", "").split("/")[-1]
                    if body_data.get("resource") else None
                )
            )

        if payment_id:
            print("PAYMENT_ID CAPTURADO:", payment_id)
            _processar_pagamento_licenca_por_payment_id(payment_id)
        else:
            print("WEBHOOK SEM PAYMENT_ID E SEM PREAPPROVAL_ID")

        return JsonResponse({"ok": True})

    except Exception as e:
        print("ERRO WEBHOOK LICENCA:", e)
        return JsonResponse({"ok": False, "erro": str(e)})