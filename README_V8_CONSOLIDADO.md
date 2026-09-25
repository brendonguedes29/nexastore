# Nexa Gestão B2B — V8 consolidado

Revisão sobre a V7 preservando infraestrutura de pagamento/licença e adicionando a consolidação solicitada durante os testes.

Principais alterações:
- correção do CSRF no formulário de atribuição de treinamento;
- campos DateField/DateTimeField renderizados como seletores de data/hora;
- listas CRUD com registros em blocos, separadores e principais informações visíveis;
- nome da empresa centralizado no cabeçalho do Centro de Gestão;
- Portal da Empresa redesenhado como entrada compartilhável da equipe, sem vitrine comercial;
- Portal do Colaborador enriquecido com notificações no topo, trilhas, tarefas, XP, ferramentas, academia e ranking;
- cadastro de colaborador por convite: gestor não define senha; colaborador ativa e cria a própria senha;
- treinamento LGPD padrão separado da governança LGPD;
- trilhas com data de início + prazo final;
- experiência de trilha em slides/etapas animadas;
- mini tutoriais animados antes das ferramentas da qualidade;
- XP automático em tarefas concluídas, aplicações de ferramentas e registros concluídos elegíveis;
- limpeza adicional de textos legados no financeiro/licença/erro CSRF;
- remoção de logs que exibiam prefixo da chave Brevo.

Validação local possível neste ambiente:
- `python -m compileall` executado com sucesso.
- `python manage.py check` não pôde ser executado porque o ambiente de construção não possui Django instalado e não tem acesso de rede para instalar requirements. O Render continuará instalando requirements no build antes de executar migrate/checks operacionais.

Migração nova: `gestao/migrations/0007_aprendizagem_prazos.py` (aditiva; adiciona `inicio` à atribuição de trilha).
