# Nexa Gestão B2B — v4 pré-GitHub

Versão de consolidação antes do GitHub. Mantém a infraestrutura existente de autenticação, ativação por e-mail, licença e Mercado Pago, e amplia a camada de gestão B2B.

## Incluído
- Centro de Gestão B2B e portal do colaborador.
- Processos, indicadores, planos 5W2H, NC/CAPA, documentos, auditorias, ISO 9001, FMEA e OEE.
- Laboratório visual: PDCA, Ishikawa 6M, 5 Porquês, Pareto com gráfico no navegador, SIPOC, MASP e 5S.
- Workspace/notas e quadro de tarefas com movimentação de status.
- Setores, colaboradores, treinamentos, XP, níveis, conquistas e simulação educativa de phishing.
- Central LGPD: inventário de tratamentos, solicitações de titulares com protocolo, incidentes de privacidade e trilha de evidências.
- Migração 0003 para os novos registros de compliance/gamificação.

## Infraestrutura preservada
As rotas existentes de Mercado Pago, callback e webhooks permanecem no projeto. O fluxo de cadastro continua com usuário inativo até confirmação por e-mail.

## Implantação
Antes de produção: backup do banco, instalar requirements, executar `python manage.py check`, `python manage.py migrate` e smoke tests de cadastro/ativação/login/licença/pagamento/webhooks.

## LGPD
O módulo é ferramenta de governança e evidência. Ele não substitui análise jurídica/organizacional nem garante conformidade isoladamente.
