from django.contrib import admin
from .models import Produto, ProdutoImagem


class ProdutoImagemInline(admin.TabularInline):
    model = ProdutoImagem
    extra = 3  # quantidade de campos extras pra upload
    fields = ("imagem", "ordem")
    ordering = ("ordem",)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "loja", "preco", "ativo")
    list_filter = ("loja", "ativo")
    search_fields = ("nome",)

    inlines = [ProdutoImagemInline]