# Nexa Gestão B2B — Release Candidate v6

Versão consolidada antes do GitHub. Mantém o núcleo legado de autenticação, ativação por e-mail, licença e Mercado Pago, e adiciona a camada B2B de qualidade, processos, pessoas e compliance.

## Consolidação funcional
- Centro de Gestão e dashboards.
- Processos, indicadores/KPIs, planos 5W2H, NC/CAPA, documentos, auditorias, ISO 9001, FMEA e OEE.
- Ferramentas guiadas: PDCA, Ishikawa, 5 Porquês, Pareto, SIPOC, MASP e 5S.
- Workspace de notas, tarefas/Kanban, comentários e colaboração.
- Setores e colaboradores.
- Perfil profissional com foto, bio, XP, nível, conquistas e privacidade.
- Ranking geral e por ferramenta; reconhecimentos e metas/desafios de equipe.
- Academia com simulações funcionais de phishing, desperdícios Lean e causa raiz.
- LGPD: inventário de tratamentos, registros, direitos dos titulares e incidentes.
- Central de notificações e trilha de auditoria.

## Infraestrutura preservada
As rotas existentes de conexão/callback/webhooks do Mercado Pago e o fluxo de ativação de conta não foram removidos. Não remover migrations antigas nem apps legados antes de validar dependências em produção.

## Implantação segura
1. Backup do banco.
2. Subir a branch de homologação.
3. `python manage.py check`
4. `python manage.py migrate`
5. Testar cadastro -> e-mail -> ativação -> login.
6. Testar licença e Mercado Pago em ambiente controlado.
7. Só então promover para produção.

LGPD: o módulo auxilia governança e evidências, mas conformidade jurídica depende também das práticas, contratos, políticas e bases legais reais da organização.
