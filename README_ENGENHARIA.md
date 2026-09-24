# NexaStore — Gestão, Qualidade e Engenharia

Reconstrução da NexaStore sobre a infraestrutura original.

## Arquitetura reaproveitada
- `Loja` continua sendo a entidade técnica central para evitar quebra de banco/licença; na interface ela representa **Empresa**.
- Mercado Pago, callbacks, webhooks, assinatura e `PagamentoLicenca` foram preservados.
- O antigo storefront por subdomínio virou **Portal da Empresa**.
- O antigo painel comercial foi preservado em `/painel-legado/`; `/painel/` agora é o Centro de Gestão.
- Admin continua sendo a central do operador NexaStore.

## Módulos novos
Processos, KPIs, 5W2H, não conformidades/CAPA, documentos, auditorias, ISO 9001, FMEA, OEE, ferramentas Lean e Academia NexaStore.

## Segurança operacional
Não altere as URLs existentes de Mercado Pago nem as variáveis do Render sem validar callbacks. Antes de produção, rode migrations e teste pagamentos/licenças em ambiente controlado.

## Deploy
1. `pip install -r requirements.txt`
2. `python manage.py migrate`
3. `python manage.py collectstatic --noinput`
4. `gunicorn plataforma.wsgi:application`

Recomendação: no Render, use Build Command `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`.
