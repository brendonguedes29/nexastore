# V12 — Cronograma metodológico das ferramentas

Incremento sobre a V11.

- Cada nova aplicação no Laboratório de Qualidade cria automaticamente etapas recomendadas conforme a ferramenta: PDCA, 5W2H, Ishikawa, 5 Porquês, Pareto, SIPOC, MASP e 5S.
- 5W2H passa a ser criado dentro do Laboratório, mantendo os sete campos metodológicos e abrindo um cronograma operacional depois do cadastro.
- Cada etapa permite responsável, início, previsão, status, conclusão real, observações e evidência/anexo.
- Etapas adicionais podem ser criadas livremente para adaptar o programa à empresa.
- Ao atribuir/trocar responsável, o colaborador recebe notificação interna e tentativa de e-mail pelo serviço já existente.
- Etapas com prazo entram no motor de alertas de 7 dias, 1 dia, vencimento e atraso.
- Ao concluir uma etapa atribuída, o colaborador recebe 10 pontos automaticamente, uma única vez, com notificação de recompensa.
- Atualizações de etapa entram na trilha de auditoria.

Migration nova: `0011_etapas_cronograma_qualidade.py`.

Antes do deploy: `python manage.py check` e `python manage.py makemigrations --check --dry-run`.
