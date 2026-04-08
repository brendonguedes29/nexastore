from django.contrib import admin, messages
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.db.models import Sum
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from .models import Loja, PagamentoLicenca


class CustomAdminSite(AdminSite):
    site_header = "Painel Administrativo"
    site_title = "Administração"
    index_title = "Dashboard"

    def index(self, request, extra_context=None):
        hoje = timezone.localdate()
        inicio_mes = hoje.replace(day=1)

        pagamentos_aprovados_mes = PagamentoLicenca.objects.filter(
            status="aprovado",
            data_criacao__gte=inicio_mes
        )

        pagamentos_pendentes = PagamentoLicenca.objects.filter(
            status="pendente"
        )

        total_recebido_mes = pagamentos_aprovados_mes.aggregate(
            total=Sum("valor")
        )["total"] or 0

        total_pendente = pagamentos_pendentes.aggregate(
            total=Sum("valor")
        )["total"] or 0

        extra_context = extra_context or {}
        extra_context.update({
            "dashboard_total_lojas": Loja.objects.count(),
            "dashboard_lojas_ativas": Loja.objects.filter(ativa=True).count(),
            "dashboard_lojas_pendentes": Loja.objects.filter(status_licenca="pendente").count(),
            "dashboard_lojas_vencidas": Loja.objects.filter(status_licenca="vencida").count(),
            "dashboard_total_usuarios": User.objects.count(),
            "dashboard_total_recebido_mes": total_recebido_mes,
            "dashboard_total_pendente": total_pendente,
        })

        return super().index(request, extra_context=extra_context)


custom_admin_site = CustomAdminSite(name="custom_admin")


@admin.register(Loja, site=custom_admin_site)
class LojaAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "dono",
        "status_licenca_badge",
        "ativa_badge",
    )

    list_filter = (
        "ativa",
        "status_licenca",
    )

    search_fields = (
        "nome",
        "dono__username",
        "dono__email",
        "email_comercial",
    )

    actions = ["enviar_reset_senha"]

    def status_licenca_badge(self, obj):
        cores = {
            "ativa": ("#dcfce7", "#166534", "ATIVA"),
            "pendente": ("#fef3c7", "#92400e", "PENDENTE"),
            "vencida": ("#fee2e2", "#991b1b", "VENCIDA"),
        }
        fundo, cor, texto = cores.get(
            obj.status_licenca,
            ("#e5e7eb", "#374151", str(obj.status_licenca).upper())
        )
        return mark_safe(
            f'<span style="background:{fundo};color:{cor};padding:6px 10px;border-radius:999px;font-weight:700;font-size:12px;">{texto}</span>'
        )
    status_licenca_badge.short_description = "Status"

    def ativa_badge(self, obj):
        if obj.ativa:
            return mark_safe('<span style="color:#16a34a;font-weight:700;">● Ativa</span>')
        return mark_safe('<span style="color:#dc2626;font-weight:700;">● Inativa</span>')
    ativa_badge.short_description = "Ativa"

    @admin.action(description="🔐 Enviar redefinição de senha por e-mail")
    def enviar_reset_senha(self, request, queryset):
        enviados = 0

        for loja in queryset:
            if loja.dono and loja.dono.email:
                user = loja.dono

                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                domain = get_current_site(request).domain

                html = render_to_string("senha/email.html", {
                    "user": user,
                    "loja": loja,
                    "domain": domain,
                    "uid": uid,
                    "token": token,
                })

                send_mail(
                    "Recuperação de acesso - NexaStore",
                    "",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html,
                )

                enviados += 1

        self.message_user(
            request,
            f"{enviados} e-mail(s) de redefinição enviados com sucesso.",
            messages.SUCCESS
        )


@admin.register(PagamentoLicenca, site=custom_admin_site)
class PagamentoLicencaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "loja",
        "tipo_pagamento",
        "valor_formatado",
        "status_badge",
        "data_criacao",
    )

    list_filter = (
        "status",
        "tipo_pagamento",
        "data_criacao",
    )

    search_fields = (
        "loja__nome",
        "external_reference",
    )

    def valor_formatado(self, obj):
        return f"R$ {obj.valor:.2f}"

    def status_badge(self, obj):
        cores = {
            "pendente": ("#fef3c7", "#92400e"),
            "aprovado": ("#dcfce7", "#166534"),
            "recusado": ("#fee2e2", "#991b1b"),
        }
        fundo, cor = cores.get(obj.status, ("#e5e7eb", "#374151"))
        return mark_safe(
            f'<span style="background:{fundo};color:{cor};padding:6px 10px;border-radius:999px;font-weight:700;font-size:12px;">{obj.status.upper()}</span>'
        )


custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(Group, GroupAdmin)