# Nexa Gestão V15 — Portal, Simulações e Prazos

## Entregas
- Portal do colaborador com páginas próprias para Meus Indicadores, Meus Treinamentos e Minhas Notas.
- Treinamentos Nexa continuam separados dos treinamentos criados pela empresa; ambos participam da progressão de pontos.
- Status visual de treinamento Nexa: não iniciado, em andamento e concluído.
- Acesso de aplicação prática às ferramentas da qualidade para colaboradores.
- Simulações remodeladas com interface interativa: Caixa de Entrada Segura, Caça aos Desperdícios e Detetive da Causa Raiz.
- Sessões têm quantidade finita de rodadas e resultado final.
- Recompensa das simulações limitada a uma vez por semana ISO por colaborador e por simulação. Repetições no mesmo ciclo ficam disponíveis como prática, sem novos pontos.
- Motor de prazos ampliado: alertas em 10, 5, 2 e 0 dias, além de atraso, sem duplicar o mesmo alerta.
- Cobertura de prazo ampliada para tarefas, planos, NC, auditorias, documentos, treinamentos, etapas de qualidade, ISO 9001, ações FMEA, projetos/ferramentas da qualidade e indicadores.

## Operação
O comando `python manage.py processar_alertas` deve ser executado de forma recorrente no ambiente de produção (recomendado: uma vez ao dia) para materializar os alertas de prazo. A interface por si só não substitui o agendamento desse comando.
