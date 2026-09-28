# V30 — Ferramentas executáveis + 5S guiado

- Corrige permissão para o colaborador que criou uma análise poder desenvolver e editar suas próprias etapas.
- Adiciona ação explícita **Iniciar etapa** e salvamento contínuo de evolução.
- Gera previsões iniciais das etapas com base no período geral informado.
- Reescreve orientações metodológicas de PDCA, 5W2H, Ishikawa, 5 Porquês, Pareto, SIPOC, MASP e 5S.
- 5S passa a ter fluxo guiado: Seiri, Seiton, Seiso, Seiketsu, Shitsuke e plano/reavaliação.
- Redesenha a tela de execução para reduzir cartões/balões grandes e transformar o histórico em fluxo operacional compacto.
- Troca link cru de retorno por ação visual padronizada.
- Mantém evidências, responsáveis, previsões, status, histórico e pontuação já existentes.

## Revisão estrutural final da V30
- Sidebar/menu acompanha a altura real de qualquer página, até o fim do conteúdo, com mínimo de 100vh.
- Removido o `height:100vh` fixo que fazia o fundo do menu terminar antes de páginas longas.
- Portal do colaborador não mantém mais uma coluna lateral longa criando corredor vazio: os painéis auxiliares fluem abaixo do conteúdo em grade responsiva.
- Dashboard do gestor deixa de usar duas pilhas verticais concorrentes; os cards passam a fluir em grade responsiva conforme a própria altura.
- Regras aplicadas na base para gestor e colaborador, sem depender de correção individual por aba para a altura do menu.
