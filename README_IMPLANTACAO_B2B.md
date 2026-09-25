# Nexa Gestão — pacote B2B

Esta versão reaproveita a infraestrutura do projeto NexaStore e troca o foco funcional de e-commerce para gestão empresarial, qualidade, processos e capacitação.

## Preservado
- Mercado Pago: PIX, cartão, callbacks e webhooks existentes.
- Cadastro de empresa, autenticação, recuperação de acesso e ativação por e-mail.
- Modelo de licença/assinatura e página financeira existente.
- Configurações de banco, Cloudinary, domínio e middleware.
- URLs legadas permanecem no projeto para evitar quebra de dependências.

## Novo núcleo
- Centro de Gestão executivo.
- Setores e colaboradores com acesso individual.
- Tarefas/projetos em quadro visual, prioridade, responsável, início e fim.
- Workspace de notas rápidas.
- Processos, indicadores, 5W2H, NC/CAPA, documentos, auditorias, ISO 9001, FMEA e OEE.
- Laboratório guiado: PDCA, Ishikawa, 5 Porquês, Pareto, SIPOC, MASP e 5S.
- Academia e gamificação com XP/nível e histórico de tentativas.
- Simulação educativa "Phishing ou legítimo?" com 5 cenários, sem coletar credenciais.
- Portal do Colaborador.
- Registros de LGPD/privacidade com finalidade, base legal, solicitações e trilha de evidência.

## Fluxo preservado
Empresa cria conta -> recebe e-mail -> ativa conta -> login -> Centro de Gestão.
Sem plano ativo, o Centro de Gestão é visível e os módulos premium direcionam para ativação do plano. Com plano ativo, as ferramentas são liberadas.

## Deploy
Depois de substituir os arquivos na branch e o Render concluir o build, execute migrations normalmente. O pacote inclui `gestao/migrations/0002_b2b_workspace_gamificacao_lgpd.py`.

## Importante sobre LGPD
O módulo fornece recursos técnicos de governança e registro. Isso não significa, isoladamente, conformidade jurídica automática. Política de privacidade, termos, papéis de controlador/operador, retenção, subprocessadores, resposta a incidentes e bases legais devem refletir a operação real da plataforma e ser revisados antes da oferta comercial.
