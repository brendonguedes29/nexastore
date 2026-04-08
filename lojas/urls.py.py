from django.urls import path
from . import views

app_name = "lojas"

urlpatterns = [
    path("", views.home, name="home"),

    path("loja/<slug:slug>/", views.loja_view, name="loja"),
    path("produto/<int:produto_id>/", views.produto_view, name="produto"),

    path("comprador/<slug:slug>/login/", views.login_comprador, name="login_comprador"),
    path("comprador/<slug:slug>/cadastro/", views.cadastro_comprador, name="cadastro_comprador"),
    path("comprador/logout/", views.logout_comprador, name="logout_comprador"),
    path("comprador/meus-pedidos/", views.meus_pedidos, name="meus_pedidos"),

    path("carrinho/adicionar/<int:produto_id>/", views.adicionar_carrinho, name="adicionar_carrinho"),
    path("carrinho/", views.ver_carrinho, name="ver_carrinho"),
    path("carrinho/remover/<int:produto_id>/", views.remover_carrinho, name="remover_carrinho"),
    path("carrinho/atualizar/", views.atualizar_carrinho, name="atualizar_carrinho"),

    path("checkout/", views.checkout, name="checkout"),
    path("pagamento/<str:referencia>/", views.pagina_pagamento, name="pagina_pagamento"),
    path("pagamento/<str:referencia>/status/", views.status_pagamento, name="status_pagamento"),
    path("pagamento/<str:referencia>/sucesso/", views.pagamento_sucesso, name="pagamento_sucesso"),
    path("compra-sucesso/", views.compra_sucesso, name="compra_sucesso"),

    path("login-loja/", views.login_loja, name="login_loja"),
    path("logout-loja/", views.logout_loja, name="logout_loja"),

    path("painel/", views.painel_loja, name="painel_loja"),

    path("painel/produtos/", views.lista_produtos_painel, name="lista_produtos_painel"),
    path("painel/produtos/novo/", views.cadastrar_produto, name="cadastrar_produto"),
    path("painel/produtos/<int:produto_id>/editar/", views.editar_produto, name="editar_produto"),
    path("painel/produtos/<int:produto_id>/excluir/", views.excluir_produto, name="excluir_produto"),

    path("painel/minha-loja/", views.minha_loja, name="minha_loja"),
    path("painel/minha-loja/dados/", views.editar_dados_loja, name="editar_dados_loja"),
    path("painel/minha-loja/vitrine/", views.editar_vitrine, name="editar_vitrine"),
    path("painel/minha-loja/vitrine/resetar/", views.resetar_vitrine, name="resetar_vitrine"),

    path("painel/categorias/", views.categorias, name="categorias"),
    path("painel/categorias/nova/", views.nova_categoria, name="nova_categoria"),

    path("painel/pedidos/", views.pedidos, name="pedidos"),
    path("painel/pedido/<int:pedido_id>/", views.detalhe_pedido, name="detalhe_pedido"),
    path("painel/pedido/<int:pedido_id>/status/<str:novo_status>/", views.alterar_status_pedido, name="alterar_status_pedido"),

    path("painel/clientes/", views.clientes, name="clientes"),
    path("painel/compradores/", views.compradores_painel, name="compradores_painel"),
    path("painel/comprador/<int:comprador_id>/status/", views.alterar_status_comprador, name="alterar_status_comprador"),

    path("painel/vendas/", views.vendas, name="vendas"),
    path("painel/entradas-saidas/", views.entradas_saidas, name="entradas_saidas"),
    path("painel/relatorios/", views.relatorios, name="relatorios"),
    path("painel/exportar-excel/", views.exportar_excel, name="exportar_excel"),

    path("painel/frete-entrega/", views.frete_entrega, name="frete_entrega"),
    path("painel/frete/config/", views.editar_config_frete, name="editar_config_frete"),
    path("painel/frete/faixa/nova/", views.nova_faixa_frete, name="nova_faixa_frete"),
    path("painel/frete/faixa/<int:faixa_id>/editar/", views.editar_faixa_frete, name="editar_faixa_frete"),

    path("painel/pagamentos/", views.pagamentos_painel, name="pagamentos_painel"),
    path("painel/pagamentos/conectar/", views.conectar_mercadopago, name="conectar_mercadopago"),
    path("painel/pagamentos/callback/", views.callback_mercadopago, name="callback_mercadopago"),

    # ===== NOVO: FINANCEIRO / LICENÇA =====
    path("painel/financeiro/", views.financeiro_loja, name="financeiro_loja"),
    path("painel/financeiro/renovar/", views.renovar_licenca_manual, name="renovar_licenca_manual"),

    path("webhooks/mercadopago/", views.webhook_mercadopago, name="webhook_mercadopago"),
    path("pagamento/cartao/criar/", views.criar_pagamento_cartao, name="criar_pagamento_cartao"),
    path("pagamento/pix/criar/", views.criar_pagamento_pix, name="criar_pagamento_pix"),

    path("simular-pagamento/<str:referencia>/", views.simular_pagamento_aprovado, name="simular_pagamento_aprovado"),
]