# Nexa Gestão V14 — Pontos, UX e Simulações

## Evolução do colaborador
Faixas: Iniciante 0; Aprendiz 500; Praticante 1.200; Especialista 2.200; Referência 3.600; Mestre 5.500; Elite 8.000 pontos.
O portal mostra nível, pontos, posição no ranking, barra para próximo nível, tarefas, treinamentos e indicadores em layout mais compacto.

## Pontuação
- Treinamentos da empresa: etapas concluídas podem pontuar conforme configuração da empresa.
- Treinamentos Nexa: conteúdo separado, autoinscrição pelo colaborador, avaliação final e pontos proporcionais aos acertos (máximo padrão 150 por treinamento).
- Simulações: recompensa única por atividade para reduzir repetição artificial de pontos.
- Qualidade, tarefas e reconhecimentos continuam integrados ao histórico existente.

## Treinamentos Nexa
Campo `origem` separa `empresa` e `nexa`. Catálogo Nexa não é editor administrativo. A conclusão do conteúdo Nexa leva a uma avaliação final; nota e pontos são registrados, e certificado virtual é liberado quando a nota mínima é atingida.

## Simulações
A atividade de phishing foi transformada visualmente em uma caixa de entrada simulada. Atividades que ainda são perguntas/decisões guiadas não devem ser apresentadas como videogame.

## Migração
Nova migração: `0013_treinamento_origem.py`.

## Validação
`python -m compileall gestao lojas plataforma` passou. `python manage.py check` deve ser executado no Codespaces/Render, pois o ambiente de empacotamento não possui Django instalado.
