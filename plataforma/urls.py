from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
import lojas.views as views

from lojas.admin import custom_admin_site
from lojas.public_views import criar_loja_publica
from lojas.licenca_views import (
    financeiro_loja,
    renovar_licenca_manual,
    gerar_pix_licenca,
    gerar_checkout_licenca,
    status_pagamento_licenca,
    webhook_mercadopago_licenca,
)

from lojas.views import (
    home,
    login_loja,
    logout_loja,
    ativar_conta,
    loja_view,
    root_view,
    produto_view,
    login_comprador,
    cadastro_comprador,
    logout_comprador,
    meus_pedidos,
    adicionar_carrinho,
    ver_carrinho,
    atualizar_carrinho,
    remover_carrinho,
    checkout,
    compra_sucesso,
    pagina_pagamento,
    pagina_pagamento_cartao,
    painel_loja,
    lista_produtos_painel,
    cadastrar_produto,
    editar_produto,
    editar_dados_loja,
    editar_vitrine,
    categorias,
    nova_categoria,
    pedidos,
    detalhe_pedido,
    alterar_status_pedido,
    clientes,
    compradores_painel,
    alterar_status_comprador,
    vendas,
    entradas_saidas,
    relatorios,
    exportar_excel,
    frete_entrega,
    editar_config_frete,
    nova_faixa_frete,
    editar_faixa_frete,
    pagamentos_painel,
    conectar_mercadopago,
    callback_mercadopago,
    webhook_mercadopago,
    simular_pagamento_aprovado,
    excluir_produto,
    resetar_vitrine,
    minha_loja,
    criar_pagamento_pix,
    criar_pagamento_cartao,
    escolher_acesso,
    licenca_bloqueada,

    # LOJISTA
    recuperar_acesso_loja,
    recuperar_acesso_enviado,
    redefinir_senha_loja,
    redefinir_senha_concluida,

    # COMPRADOR
    recuperar_senha_comprador,
    recuperar_senha_comprador_enviado,
    redefinir_senha_comprador,
    redefinir_senha_comprador_concluida,

    excluir_imagem_produto,
)

urlpatterns = [

    # PÚBLICO
    path("", root_view, name="root_view"),
    path("entrar/", escolher_acesso, name="escolher_acesso"),
    path("criar-loja/", criar_loja_publica, name="criar_loja_publica"),
    path("home/", home, name="home"),

    # ADMIN
    path("admin/", custom_admin_site.urls),

    # LOGIN LOJISTA
    path("login/", login_loja, name="login_loja"),
    path("logout/", logout_loja, name="logout_loja"),

    # RECUPERAÇÃO LOJISTA
    path("login/recuperar/", recuperar_acesso_loja, name="recuperar_acesso_loja"),
    path("login/recuperar/enviado/", recuperar_acesso_enviado, name="recuperar_acesso_enviado"),
    path("login/redefinir/<uidb64>/<token>/", redefinir_senha_loja, name="redefinir_senha_loja"),
    path("login/redefinir/concluido/", redefinir_senha_concluida, name="redefinir_senha_concluida"),

    # LOJA
    path("produto/<int:produto_id>/", produto_view, name="produto"),

    # COMPRADOR
    path("comprador/<slug:slug>/login/", login_comprador, name="login_comprador"),
    path("comprador/<slug:slug>/cadastro/", cadastro_comprador, name="cadastro_comprador"),
    path("comprador/logout/", logout_comprador, name="logout_comprador"),

    # RECUPERAÇÃO DE SENHA DO COMPRADOR
    path("comprador/<slug:slug>/recuperar/", recuperar_senha_comprador, name="recuperar_senha_comprador"),
    path("comprador/<slug:slug>/recuperar/enviado/", recuperar_senha_comprador_enviado, name="recuperar_senha_comprador_enviado"),
    path("comprador/redefinir/<uidb64>/<token>/", redefinir_senha_comprador, name="redefinir_senha_comprador"),
    path("comprador/redefinir/concluido/", redefinir_senha_comprador_concluida, name="redefinir_senha_comprador_concluida"),

    path("meus-pedidos/", meus_pedidos, name="meus_pedidos"),

    # CARRINHO
    path("carrinho/", ver_carrinho, name="ver_carrinho"),
    path("carrinho/adicionar/<int:produto_id>/", adicionar_carrinho, name="adicionar_carrinho"),
    path("carrinho/remover/<int:produto_id>/", remover_carrinho, name="remover_carrinho"),
    path("carrinho/atualizar/", atualizar_carrinho, name="atualizar_carrinho"),
    path("checkout/", checkout, name="checkout"),
    path("sucesso/", compra_sucesso, name="compra_sucesso"),

    # PAGAMENTO
    path("pagamento/<str:referencia>/", pagina_pagamento, name="pagina_pagamento"),
    path("pagamento/<str:referencia>/cartao/", pagina_pagamento_cartao, name="pagina_pagamento_cartao"),
    path("pagamento/<str:referencia>/sucesso/", views.pagamento_sucesso, name="pagamento_sucesso"),
    path("api/pagamento/status/<str:referencia>/", views.status_pagamento, name="status_pagamento"),
    path("api/frete/calcular/", views.calcular_frete_ajax, name="calcular_frete_ajax"),
    path("api/pix/", criar_pagamento_pix, name="api_pix"),
    path("api/cartao/", criar_pagamento_cartao, name="api_cartao"),

    # PAINEL LOJISTA
    path("painel/", painel_loja, name="painel_loja"),
    path("painel/produtos/", lista_produtos_painel, name="lista_produtos_painel"),
    path("painel/produtos/novo/", cadastrar_produto, name="cadastrar_produto"),
    path("painel/produtos/<int:produto_id>/editar/", editar_produto, name="editar_produto"),
    path("painel/produtos/<int:produto_id>/excluir/", excluir_produto, name="excluir_produto"),

    path("painel/produto/imagem/<int:imagem_id>/excluir/", excluir_imagem_produto, name="excluir_imagem_produto"),

    path("painel/minha-loja/", minha_loja, name="minha_loja"),
    path("painel/minha-loja/dados/", editar_dados_loja, name="editar_dados_loja"),
    path("painel/minha-loja/vitrine/", editar_vitrine, name="editar_vitrine"),
    path("painel/minha-loja/vitrine/resetar/", resetar_vitrine, name="resetar_vitrine"),

    path("painel/categorias/", categorias, name="categorias"),
    path("painel/categorias/nova/", nova_categoria, name="nova_categoria"),

    path("painel/pedidos/", pedidos, name="pedidos"),
    path("painel/pedido/<int:pedido_id>/", detalhe_pedido, name="detalhe_pedido"),
    path("painel/pedido/<int:pedido_id>/status/<str:novo_status>/", alterar_status_pedido, name="alterar_status_pedido"),

    path("painel/clientes/", clientes, name="clientes"),
    path("painel/compradores/", compradores_painel, name="compradores_painel"),
    path("painel/comprador/<int:comprador_id>/status/", alterar_status_comprador, name="alterar_status_comprador"),

    path("painel/vendas/", vendas, name="vendas"),
    path("painel/entradas-saidas/", entradas_saidas, name="entradas_saidas"),
    path("painel/relatorios/", relatorios, name="relatorios"),
    path("painel/exportar-excel/", exportar_excel, name="exportar_excel"),

    path("painel/frete-entrega/", frete_entrega, name="frete_entrega"),
    path("painel/frete/config/", editar_config_frete, name="editar_config_frete"),
    path("painel/frete/faixa/nova/", nova_faixa_frete, name="nova_faixa_frete"),
    path("painel/frete/faixa/<int:faixa_id>/editar/", editar_faixa_frete, name="editar_faixa_frete"),

    path("painel/pagamentos/", pagamentos_painel, name="pagamentos_painel"),
    path("painel/pagamentos/conectar/", conectar_mercadopago, name="conectar_mercadopago"),
    path("painel/pagamentos/callback/", callback_mercadopago, name="callback_mercadopago"),

    path("painel/financeiro/", financeiro_loja, name="financeiro_loja"),
    path("painel/financeiro/renovar/", renovar_licenca_manual, name="renovar_licenca_manual"),
    path("painel/financeiro/gerar-pix/", gerar_pix_licenca, name="gerar_pix_licenca"),
    path("painel/financeiro/gerar-checkout/", gerar_checkout_licenca, name="gerar_checkout_licenca"),
    path("painel/financeiro/status/<int:pagamento_id>/", status_pagamento_licenca, name="status_pagamento_licenca"),

    # WEBHOOK
    path("webhooks/mercadopago/", webhook_mercadopago, name="webhook_mercadopago"),
    path("webhooks/mercadopago/licenca/", webhook_mercadopago_licenca, name="webhook_mercadopago_licenca"),

    path("simular-pagamento/<str:referencia>/", simular_pagamento_aprovado, name="simular_pagamento_aprovado"),
    path("frete/faixa/excluir/<int:faixa_id>/", views.excluir_faixa_frete, name="excluir_faixa_frete"),
    path("painel/produto/imagem/<int:imagem_id>/principal/", views.definir_imagem_principal, name="definir_imagem_principal"),

    path("ativar/<uidb64>/<token>/", ativar_conta, name="ativar_conta"),
    path("remover-logo/", views.remover_logo_ajax, name="remover_logo_ajax"),
    path("painel/financeiro/status/<int:pk>/", views.status_licenca, name="status_licenca"),
    path("painel/licenca-bloqueada/", licenca_bloqueada, name="licenca_bloqueada"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)