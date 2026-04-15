from django import forms
from django.contrib.auth.models import User
from .models import Produto, Categoria, ConfigFrete, FaixaFrete


class ProdutoForm(forms.ModelForm):
    imagens_extras = forms.FileField(required=False)

    class Meta:
        model = Produto
        fields = [
            "nome",
            "categoria",
            "descricao",
            "preco",
            "custo",
            "estoque",
            "imagem",
            "ativo",
            "em_destaque",
            "produto_novo",
            "percentual_promocao",
        ]
        widgets = {
            "preco": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "custo": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "estoque": forms.NumberInput(attrs={"min": "0"}),
            "percentual_promocao": forms.NumberInput(attrs={"min": "0"}),
        }

    def clean_imagens_extras(self):
        return self.files.getlist("imagens_extras")


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nome"]


class CadastroCompradorForm(forms.Form):
    nome = forms.CharField(max_length=150)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    telefone = forms.CharField(max_length=30, required=False)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este usuário já existe.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("As senhas não coincidem.")

        return cleaned_data


class ConfigFreteForm(forms.ModelForm):
    class Meta:
        model = ConfigFrete
        fields = [
            "cep_origem",
            "rua_origem",
            "numero_origem",
            "complemento_origem",
            "bairro_origem",
            "cidade_origem",
            "estado_origem",
            "valor_fora_estado",
            "retirada_loja",
            "entrega_ativa",
        ]


class FaixaFreteForm(forms.ModelForm):
    class Meta:
        model = FaixaFrete
        fields = [
            "km_inicial",
            "km_final",
            "valor",
            "ativo",
        ]