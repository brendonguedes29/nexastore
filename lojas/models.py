from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify


TIPOS_LOJA = [
    ("roupas", "Roupas"),
    ("comida", "Comida"),
    ("cosmeticos", "Cosméticos"),
    ("eletronicos", "Eletrônicos"),
    ("acessorios", "Acessórios"),
    ("servicos", "Serviços"),
    ("outros", "Outros"),
]

STATUS_LICENCA_CHOICES = [
    ("pendente", "Pendente"),
    ("ativa", "Ativa"),
    ("vencida", "Vencida"),
]


class Loja(models.Model):
    tipo_loja = models.CharField(
        max_length=30,
        choices=TIPOS_LOJA,
        default="outros",
        verbose_name="Tipo da loja"
    )

    dono = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="loja"
    )

    nome = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    descricao = models.TextField(blank=True, null=True)

    logo = models.ImageField(upload_to="lojas/", blank=True, null=True)

    email_comercial = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=30, blank=True, null=True)
    cnpj = models.CharField(max_length=30, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)

    banner_titulo = models.CharField(max_length=150, blank=True, null=True)
    banner_subtitulo = models.CharField(max_length=255, blank=True, null=True)
    banner_botao_texto = models.CharField(max_length=100, blank=True, null=True)
    banner_botao_link = models.CharField(max_length=255, blank=True, null=True)
    banner_cor_inicio = models.CharField(max_length=20, blank=True, null=True)
    banner_cor_fim = models.CharField(max_length=20, blank=True, null=True)
    banner_imagem = models.ImageField(upload_to="banners/", blank=True, null=True)
    texto_busca = models.CharField(max_length=150, blank=True, null=True)

    ativa = models.BooleanField(default=True)

    valor_licenca = models.DecimalField(max_digits=10, decimal_places=2, default=49.90)

    data_ultimo_pagamento = models.DateField(blank=True, null=True)
    data_vencimento_licenca = models.DateField(blank=True, null=True)

    status_licenca = models.CharField(
        max_length=20,
        choices=STATUS_LICENCA_CHOICES,
        default="pendente"
    )

    link_pagamento = models.URLField(blank=True, null=True)
    chave_pix = models.CharField(max_length=255, blank=True, null=True)
    pix_copia_cola = models.TextField(blank=True, null=True)
    nome_recebedor = models.CharField(max_length=150, blank=True, null=True)
    whatsapp_financeiro = models.CharField(max_length=30, blank=True, null=True)

    aceitar_pix = models.BooleanField(default=True)
    aceitar_cartao = models.BooleanField(default=True)
    aceitar_whatsapp_financeiro = models.BooleanField(default=True)

    observacoes_licenca = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nome) or f"loja-{self.dono_id}"
            slug = base_slug
            contador = 1

            while Loja.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{contador}"
                contador += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def renovar_licenca(self, dias=30):
        hoje = timezone.localdate()

        if self.data_vencimento_licenca and self.data_vencimento_licenca >= hoje:
            nova_data_vencimento = self.data_vencimento_licenca + timedelta(days=dias)
        else:
            nova_data_vencimento = hoje + timedelta(days=dias)

        self.data_ultimo_pagamento = hoje
        self.data_vencimento_licenca = nova_data_vencimento
        self.status_licenca = "ativa"
        self.ativa = True

        self.save(update_fields=[
            "data_ultimo_pagamento",
            "data_vencimento_licenca",
            "status_licenca",
            "ativa",
            "atualizado_em",
        ])

    def verificar_licenca(self):
        hoje = timezone.localdate()

        if not self.data_vencimento_licenca:
            self.status_licenca = "pendente"
            self.ativa = False
            self.save(update_fields=["status_licenca", "ativa", "atualizado_em"])
            return

        if hoje > self.data_vencimento_licenca:
            self.status_licenca = "vencida"
            self.ativa = False
        else:
            self.status_licenca = "ativa"
            self.ativa = True

        self.save(update_fields=["status_licenca", "ativa", "atualizado_em"])

    @property
    def licenca_ativa(self):
        if not self.data_vencimento_licenca:
            return False
        return timezone.localdate() <= self.data_vencimento_licenca

    @property
    def dias_restantes_licenca(self):
        if not self.data_vencimento_licenca:
            return 0
        dias = (self.data_vencimento_licenca - timezone.localdate()).days
        return max(dias, 0)

    @property
    def pagamento_disponivel(self):
        return bool(
            (self.aceitar_pix and (self.chave_pix or self.pix_copia_cola)) or
            (self.aceitar_cartao and self.link_pagamento) or
            (self.aceitar_whatsapp_financeiro and self.whatsapp_financeiro)
        )


class PagamentoLicenca(models.Model):
    STATUS_CHOICES = [
        ("criado", "Criado"),
        ("pendente", "Pendente"),
        ("aprovado", "Aprovado"),
        ("recusado", "Recusado"),
        ("cancelado", "Cancelado"),
        ("expirado", "Expirado"),
    ]

    TIPO_CHOICES = [
        ("pix", "Pix"),
        ("checkout", "Checkout"),
    ]

    loja = models.ForeignKey(
        Loja,
        on_delete=models.CASCADE,
        related_name="pagamentos_licenca"
    )

    valor = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_pagamento = models.CharField(max_length=20, choices=TIPO_CHOICES)

    external_reference = models.CharField(max_length=120, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="criado")

    plano_nome = models.CharField(max_length=100, default="Plano padrão")

    mp_payment_id = models.CharField(max_length=120, blank=True, null=True)
    mp_preference_id = models.CharField(max_length=120, blank=True, null=True)
    mp_init_point = models.TextField(blank=True, null=True)

    qr_code = models.TextField(blank=True, null=True)
    qr_code_base64 = models.TextField(blank=True, null=True)
    ticket_url = models.TextField(blank=True, null=True)

    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    data_aprovacao = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-data_criacao"]

    def __str__(self):
        return f"{self.loja.nome} - {self.get_tipo_pagamento_display()} - {self.get_status_display()}"

    def marcar_aprovado(self):
        if self.status != "aprovado":
            self.status = "aprovado"
            self.data_aprovacao = timezone.now()
            self.save(update_fields=["status", "data_aprovacao", "data_atualizacao"])
            self.loja.renovar_licenca(30)

    def marcar_status_por_mp(self, status_mp):
        mapa = {
            "approved": "aprovado",
            "pending": "pendente",
            "in_process": "pendente",
            "rejected": "recusado",
            "cancelled": "cancelado",
            "expired": "expirado",
        }

        novo_status = mapa.get(status_mp, "pendente")

        if novo_status == "aprovado":
            self.marcar_aprovado()
        else:
            self.status = novo_status
            self.save(update_fields=["status", "data_atualizacao"])