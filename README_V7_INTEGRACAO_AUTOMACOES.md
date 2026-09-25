# Nexa Gestão v7 — integração, automações e trilhas

## Principais correções
- Login único: administrador, gestor de empresa/setor e colaborador.
- Colaborador criado em Gestão > Equipe consegue autenticar no `/login/`.
- Administrador/gestor é direcionado ao Centro de Gestão; colaborador ao Portal do Colaborador.
- Login reescrito sem linguagem de loja/e-commerce.
- Financeiro preserva Mercado Pago, mas retorna ao Centro de Gestão e usa linguagem de empresa/plano.

## Novos recursos
- Papéis: colaborador, gestor de setor e gestor da empresa.
- Gestores podem usar Academia, jogos, trilhas, perfil e XP; ranking principal mostra colaboradores por padrão.
- Dashboard com equipe/fotos, setores, agenda e próximos vencimentos.
- Treinamentos criados pela empresa com etapas/missões, vídeo, anexos, perguntas, XP, prazo e atribuição a colaboradores.
- Motor de alertas para tarefas, 5W2H, NC, auditorias, revisão documental e treinamentos.
- Avisos dentro da plataforma e suporte a e-mail pelo Brevo já existente.

## Alertas automáticos no Render
O comando abaixo cria os alertas e envia os e-mails pendentes sem duplicar o mesmo aviso/canal:

    python manage.py processar_alertas

Recomendação: depois de validar a v7, configurar um Render Cron Job diário usando o mesmo repositório/variáveis e esse comando. O dashboard também atualiza avisos internos ao ser acessado, sem disparar e-mail nessa execução.

## Implantação
1. Subir todos os arquivos desta versão para a mesma branch.
2. `python manage.py check`
3. `python manage.py makemigrations --check --dry-run` (deve reconhecer que a migration 0006 já acompanha o pacote, sem gerar migration nova)
4. `python manage.py migrate --plan`
5. Deploy. O Build Command existente continuará executando `migrate`.

## Núcleo financeiro preservado
As rotas e funções existentes de Mercado Pago, PIX, checkout, callback, assinatura e webhooks não foram removidas. A alteração no financeiro foi de navegação/texto para o contexto B2B.
