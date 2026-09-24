from django import forms
from .models import Loja


CORES_BANNER = [
    ("#16a34a", "Verde"),
    ("#2563eb", "Azul"),
    ("#ffffff", "Branco"),
    ("#111827", "Preto"),
    ("#1f2937", "Cinza escuro"),
    ("#e5e7eb", "Cinza claro"),
    ("#dc2626", "Vermelho"),
    ("#f97316", "Laranja"),
    ("#7c3aed", "Roxo"),
    ("#0f766e", "Verde petróleo"),
]


class LojaDadosForm(forms.ModelForm):
    remover_logo = forms.BooleanField(
        required=False,
        label="Remover logo atual",
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Loja
        fields = [
            "nome",
            "tipo_loja",
            "email_comercial",
            "telefone",
            "cnpj",
            "endereco",
            "descricao",
            "logo",
            "ativa",
            "valor_licenca",
            "link_pagamento",
            "chave_pix",
            "pix_copia_cola",
            "nome_recebedor",
            "whatsapp_financeiro",
            "aceitar_pix",
            "aceitar_cartao",
            "aceitar_whatsapp_financeiro",
            "observacoes_licenca",
        ]

        labels = {
            "nome": "Nome da loja",
            "tipo_loja": "Tipo da loja",
            "email_comercial": "E-mail comercial",
            "telefone": "Telefone",
            "cnpj": "CNPJ",
            "endereco": "Endereço",
            "descricao": "Descrição",
            "logo": "Logo da loja",
            "ativa": "Loja ativa",
            "valor_licenca": "Valor da licença",
            "link_pagamento": "Link de pagamento",
            "chave_pix": "Chave Pix",
            "pix_copia_cola": "Pix copia e cola",
            "nome_recebedor": "Nome do recebedor",
            "whatsapp_financeiro": "WhatsApp financeiro",
            "aceitar_pix": "Aceitar Pix",
            "aceitar_cartao": "Aceitar cartão / link",
            "aceitar_whatsapp_financeiro": "Aceitar atendimento via WhatsApp",
            "observacoes_licenca": "Observações da licença",
        }

        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 4}),
            "pix_copia_cola": forms.Textarea(attrs={"rows": 4}),
            "observacoes_licenca": forms.Textarea(attrs={"rows": 4}),
            "valor_licenca": forms.NumberInput(attrs={"step": "0.01"}),
        }


class LojaVitrineForm(forms.ModelForm):
    banner_cor_inicio = forms.ChoiceField(
        choices=CORES_BANNER,
        required=False
    )

    banner_cor_fim = forms.ChoiceField(
        choices=CORES_BANNER,
        required=False
    )

    remover_banner_imagem = forms.BooleanField(
        required=False
    )

    class Meta:
        model = Loja
        fields = [
            "banner_titulo",
            "banner_subtitulo",
            "banner_botao_texto",
            "banner_botao_link",
            "banner_cor_inicio",
            "banner_cor_fim",
            "banner_imagem",
            "texto_busca",
        ]

    def save(self, commit=True):
        loja = super().save(commit=False)

        if self.cleaned_data.get("remover_banner_imagem"):
            if loja.banner_imagem:
                loja.banner_imagem.delete(save=False)
            loja.banner_imagem = None

        if commit:
            loja.save()

        return loja


class LojaForm(forms.ModelForm):
    banner_cor_inicio = forms.ChoiceField(choices=CORES_BANNER, required=False)
    banner_cor_fim = forms.ChoiceField(choices=CORES_BANNER, required=False)
    remover_banner_imagem = forms.BooleanField(required=False)
    remover_logo = forms.BooleanField(required=False, label="Remover logo atual")

    class Meta:
        model = Loja
        fields = [
            "nome",
            "tipo_loja",
            "email_comercial",
            "telefone",
            "cnpj",
            "endereco",
            "descricao",
            "logo",
            "ativa",
            "valor_licenca",
            "link_pagamento",
            "chave_pix",
            "pix_copia_cola",
            "nome_recebedor",
            "whatsapp_financeiro",
            "aceitar_pix",
            "aceitar_cartao",
            "aceitar_whatsapp_financeiro",
            "observacoes_licenca",
            "banner_titulo",
            "banner_subtitulo",
            "banner_botao_texto",
            "banner_botao_link",
            "banner_cor_inicio",
            "banner_cor_fim",
            "banner_imagem",
            "texto_busca",
        ]

    def save(self, commit=True):
        loja = super().save(commit=False)

        if self.cleaned_data.get("remover_logo"):
            if loja.logo:
                loja.logo.delete(save=False)
            loja.logo = None

        if self.cleaned_data.get("remover_banner_imagem"):
            if loja.banner_imagem:
                loja.banner_imagem.delete(save=False)
            loja.banner_imagem = None

        if commit:
            loja.save()

        return loja