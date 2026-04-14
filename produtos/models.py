from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from lojas.models import Loja


class Categoria(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Comprador(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name="compradores")
    telefone = models.CharField(max_length=30, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.loja.nome}"


class Produto(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    nome = models.CharField(max_length=200)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    custo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descricao = models.TextField()
    ativo = models.BooleanField(default=True)
    em_destaque = models.BooleanField(default=False)
    produto_novo = models.BooleanField(default=False)
    percentual_promocao = models.PositiveIntegerField(default=0)
    imagem = models.ImageField(upload_to="produtos/", blank=True, null=True)
    estoque = models.IntegerField(default=0)

    def __str__(self):
        return self.nome

    @property
    def em_promocao(self):
        return self.percentual_promocao > 0

    @property
    def preco_promocional(self):
        if self.percentual_promocao and self.percentual_promocao > 0:
            desconto = (Decimal(self.percentual_promocao) / Decimal("100")) * self.preco
            return self.preco - desconto
        return self.preco

    @property
    def preco_com_desconto(self):
        if self.percentual_promocao and self.percentual_promocao > 0:
            desconto = (Decimal(self.percentual_promocao) / Decimal("100")) * self.preco
            return self.preco - desconto
        return self.preco

    @property
    def valor_estoque(self):
        return self.custo * self.estoque


class ProdutoImagem(models.Model):
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name="imagens_extras"
    )
    imagem = models.ImageField(upload_to="produtos/extras/")
    ordem = models.PositiveIntegerField(default=0)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordem", "id"]
        verbose_name = "Imagem do produto"
        verbose_name_plural = "Imagens do produto"

    def __str__(self):
        return f"Imagem de {self.produto.nome}"


class ConfigFrete(models.Model):
    loja = models.OneToOneField(Loja, on_delete=models.CASCADE, related_name="config_frete")

    cep_origem = models.CharField(max_length=20, blank=True, null=True)
    rua_origem = models.CharField(max_length=150, blank=True, null=True)
    numero_origem = models.CharField(max_length=20, blank=True, null=True)
    complemento_origem = models.CharField(max_length=150, blank=True, null=True)
    bairro_origem = models.CharField(max_length=100, blank=True, null=True)
    cidade_origem = models.CharField(max_length=100, blank=True, null=True)
    estado_origem = models.CharField(max_length=50, blank=True, null=True)

    km_max_local = models.DecimalField(max_digits=6, decimal_places=2, default=15)
    valor_excedente = models.DecimalField(max_digits=10, decimal_places=2, default=30)
    valor_fora_estado = models.DecimalField(max_digits=10, decimal_places=2, default=50)

    retirada_loja = models.BooleanField(default=True)
    entrega_ativa = models.BooleanField(default=True)

    chave_pix = models.CharField(max_length=150, blank=True, null=True)
    nome_recebedor_pix = models.CharField(max_length=150, blank=True, null=True)
    banco_pix = models.CharField(max_length=100, blank=True, null=True)

    mp_connected = models.BooleanField(default=False)
    mp_user_id = models.CharField(max_length=100, blank=True, null=True)
    mp_access_token = models.TextField(blank=True, null=True)
    mp_refresh_token = models.TextField(blank=True, null=True)
    mp_public_key = models.CharField(max_length=255, blank=True, null=True)
    mp_token_expires_in = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"Configuração da loja - {self.loja.nome}"


class FaixaFrete(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name="faixas_frete")
    km_inicial = models.DecimalField(max_digits=6, decimal_places=2)
    km_final = models.DecimalField(max_digits=6, decimal_places=2)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.km_inicial}km - {self.km_final}km = R$ {self.valor}"


class Pedido(models.Model):
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("aguardando_envio", "Aguardando envio"),
        ("enviado", "Enviado"),
        ("saiu_entrega", "Saiu para entrega"),
        ("entregue", "Entregue"),
        ("cancelado", "Cancelado"),
    ]

    PAGAMENTO_CHOICES = [
        ("pix", "Pix"),
        ("dinheiro", "Dinheiro"),
        ("cartao", "Cartão"),
    ]

    TIPO_CARTAO_CHOICES = [
        ("", "Não se aplica"),
        ("debito", "Débito"),
        ("credito", "Crédito"),
    ]

    STATUS_PAGAMENTO_CHOICES = [
        ("aguardando", "Aguardando pagamento"),
        ("confirmacao", "Aguardando confirmação"),
        ("pago", "Pago"),
        ("recusado", "Recusado"),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    comprador = models.ForeignKey(Comprador, on_delete=models.SET_NULL, null=True, blank=True)

    nome_cliente = models.CharField(max_length=150)
    quantidade = models.IntegerField(default=1)

    telefone = models.CharField(max_length=30, blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    forma_pagamento = models.CharField(max_length=20, choices=PAGAMENTO_CHOICES, default="pix")
    tipo_cartao = models.CharField(max_length=20, choices=TIPO_CARTAO_CHOICES, blank=True, default="")
    observacao = models.TextField(blank=True, null=True)

    cep_entrega = models.CharField(max_length=20, blank=True, null=True)
    rua_entrega = models.CharField(max_length=150, blank=True, null=True)
    numero_entrega = models.CharField(max_length=20, blank=True, null=True)
    complemento_entrega = models.CharField(max_length=150, blank=True, null=True)
    bairro_entrega = models.CharField(max_length=100, blank=True, null=True)
    cidade_entrega = models.CharField(max_length=100, blank=True, null=True)
    estado_entrega = models.CharField(max_length=50, blank=True, null=True)

    distancia_km = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    valor_frete = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status_pagamento = models.CharField(max_length=20, choices=STATUS_PAGAMENTO_CHOICES, default="aguardando")
    referencia_pagamento = models.CharField(max_length=120, blank=True, null=True)
    data_pagamento = models.DateTimeField(blank=True, null=True)

    mp_payment_id = models.CharField(max_length=120, blank=True, null=True)
    mp_qr_code = models.TextField(blank=True, null=True)
    mp_qr_code_base64 = models.TextField(blank=True, null=True)
    mp_ticket_url = models.TextField(blank=True, null=True)

    data = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente")

    def __str__(self):
        return f"Pedido {self.id} - {self.nome_cliente}"


class MovimentacaoEstoque(models.Model):
    TIPO_CHOICES = [
        ("entrada", "Entrada"),
        ("saida", "Saída"),
    ]

    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.IntegerField()
    motivo = models.CharField(max_length=100)
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.produto.nome} - {self.quantidade}"