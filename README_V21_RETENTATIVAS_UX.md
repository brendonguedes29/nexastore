# Nexa Gestão V21 — Retentativas, revisão e refinamento visual

Base: V20 (apresentações com múltiplos slides).

## Avaliação final
- Nota mínima continua configurável; aprovação não exige 100%.
- Gestor define 1, 2, 3, 5 ou tentativas ilimitadas na etapa de avaliação final.
- Cada envio da avaliação final grava tentativa, nota, acertos, data e resultado.
- Reprovação não conclui a etapa, não emite certificado e não concede os pontos da etapa.
- Colaborador pode revisar as etapas anteriores e voltar à avaliação.
- Ao atingir o limite, novos envios são bloqueados no backend e na interface.
- Treinamento concluído continua em modo de revisão, sem duplicar pontos.

## UX
- Resultado da avaliação ganhou cartão visual com nota, mínimo, tentativa e tentativas restantes.
- Central de notificações ganhou lista mais limpa, hierarquia visual e estado de não lida.
- Portal do colaborador destaca a empresa no topo.
- Tipografia, mensagens e hierarquia visual receberam refinamento global conservador.

## Banco
Migration nova: `0020_tentativas_avaliacao.py`.
