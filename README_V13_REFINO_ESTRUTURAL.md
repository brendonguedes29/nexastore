# Nexa Gestão V13 — Refino estrutural

## Principais mudanças
- Separação de experiência entre gestor da empresa e colaborador/gestor de setor.
- Ranking inclui colaboradores ativos elegíveis mesmo com 0 pontos e independentemente do papel operacional.
- Treinamentos Nexa viraram catálogo didático/visual e não abrem mais a tela de autoria.
- ISO 9001 atualizada para ISO 9001:2026 com roteiro guiado dos blocos 4 a 10, observações, prazo e evidências.
- FMEA ampliado para múltiplos modos de falha por processo, controles, ação, responsável, prazo, status e reavaliação S/O/D.
- OEE com explicação visual de Disponibilidade, Performance, Qualidade e cálculo.
- Arquivos de Gestão Documental, evidências ISO e materiais de treinamento usam armazenamento Cloudinary RAW para documentos não-imagem.
- E-mail de ativação reposicionado para Nexa Gestão e plano inicial de R$ 199,00/mês.
- Migração de preço atualiza apenas empresas ainda em R$ 59,90 para R$ 199,00.
- Cache desabilitado no layout para reduzir contador de notificações visualmente defasado após leitura.

## Migrações
- gestao 0012_refino_iso_fmea_arquivos
- lojas 0014_valor_licenca_nexa_gestao

## Validação
- Python compileall: aprovado.
- `python manage.py check` deve ser executado no Codespaces/Render, pois o ambiente de empacotamento não possui Django instalado.
