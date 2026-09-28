# Nexa Gestão V29 — Correção Global Real

Foco desta versão: corrigir a fundação visual que permaneceu incompleta na V28, sem criar migrations.

- Dashboard do gestor refeito em duas pilhas independentes: cards não herdam altura da coluna vizinha e estados vazios ficam compactos.
- OEE deixa de usar histórico largo + formulário espremido. Nova medição ocupa largura total em grid responsivo; histórico fica abaixo.
- Sistema global de formulários: checkbox vira switch proporcional, radio compacto, divisores, espaçamento consistente e inputs limitados à largura útil.
- Cabeçalho do colaborador reduzido e mais denso.
- Links de ação padronizados para não parecerem hyperlinks HTML crus.
- Portal público: botões de entrar/cadastro com gap e proporção corrigidos.
- Perfil do colaborador recebe layout compacto explícito, inclusive toggles.
- Regras globais reforçam altura por conteúdo e evitam cards esticados.

Validação local do pacote: compilação Python e integridade ZIP. Executar `python manage.py check` no projeto completo antes do commit.
