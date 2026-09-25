# Nexa Gestão B2B — V9 Consolidado

Esta versão parte da V8 e consolida a rodada de testes de 25/09/2026.

## Melhorias principais
- Histórico das ferramentas agora é clicável e abre uma visualização completa da análise.
- Histórico mostra ferramenta, título, processo, setor, status, criação e prazo/conclusão.
- Visão Geral ganhou atividade recente e análises recentes, inclusive registros já existentes.
- Cabeçalho global ganhou área de notificações; quando há pendências, aparece alerta vermelho e contador.
- Portal público da empresa ganhou rota estável `/empresa/<slug>/` e acesso direto pelo Centro de Gestão.
- Centro de Gestão mostra o link do Portal dos Colaboradores para abrir/copiar.
- FMEA, Indicadores, NC e demais formulários com Processo permitem criar processo rapidamente sem abandonar a tela.
- Processo passa a poder ser relacionado a um setor.
- Ferramentas do Laboratório passam a registrar processo, setor, início, prazo/conclusão e status.
- Mini-aulas das ferramentas ganharam tratamento visual e animação mais evidente.
- Trilhas de treinamento ganharam ilustrações SVG por contexto (LGPD, qualidade e aprendizagem geral), mantendo animação e progressão.
- Registros CRUD mostram datas e campos principais com separação visual.
- Salvamentos relevantes geram registro de auditoria para alimentar a Visão Geral.
- Revisão estática de nomes de rotas/templates e aliases de compatibilidade para links legados `loja`/`loja_view`.
- Texto legado remanescente no financeiro foi ajustado sem alterar a infraestrutura de pagamento.

## Banco de dados
Nova migração aditiva: `gestao/migrations/0008_historico_portal_intuitivo.py`.
Ela adiciona relações opcionais e não remove dados existentes.

## Validação realizada
- `python -m compileall`: OK.
- Varredura estática de `{% url %}`, `redirect()` e `reverse()` para detectar nomes de rotas ausentes.
- `python manage.py check` não pôde ser executado no ambiente de empacotamento porque Django não está instalado nele. O Render instalará `requirements.txt` antes do build e executará as migrações pelo comando já configurado.

## Importante
Preservados `requirements.txt`, configurações por variáveis de ambiente, banco, Mercado Pago, callbacks/webhooks, Brevo, ativação de conta e fluxo de licença.
