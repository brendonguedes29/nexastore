# Nexa Gestão V17 — Persistência, permissões e treinamentos

Base: V16 / commit de produção informado 3b27253.

## Principais mudanças
- Ferramentas de qualidade: etapas persistentes no mesmo registro, painel visual por etapa, status automático em andamento ao registrar execução, atraso visual por prazo, conclusão automática do registro quando todas as etapas são concluídas e histórico/auditoria preservados.
- Permissões: análises são isoladas por empresa e, para colaboradores, por setor ou atribuição direta. Colaborador só edita etapa pela qual é responsável; gestão mantém controle geral. Projeto agora registra `criado_por`.
- UI: detalhe de análise reorganizado em cartões compactos/expansíveis, status visual e formulários em grade.
- Treinamentos: treinamento sem etapas ganha conteúdo principal automaticamente (evita “trilha concluída” ao primeiro clique); abrir treinamento muda Pendente → Em andamento; vídeo do YouTube é incorporado; conteúdo/descrição aparece ao colaborador; progresso percentual corrigido.
- Autor: tela de treinamento reorganizada, com edição de dados principais, vídeo, etapas/slides, materiais/checkpoints e atribuição à equipe.
- Formulários: refinamento global de labels, espaçamento, foco e campos.

## Migração
`gestao/migrations/0015_projetoqualidade_criado_por.py`

## Validação
Os arquivos Python foram compilados com `py_compile`. O ambiente de geração não possui Django instalado, portanto execute no Codespaces:
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`

Não execute `migrate` no Codespaces; o build do Render já executa migrations.
