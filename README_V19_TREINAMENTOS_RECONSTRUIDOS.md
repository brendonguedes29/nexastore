# Nexa Gestão V19 — Treinamentos reconstruídos

Base: V17 completa + alterações V18 já implantadas + correções V19.

Principais mudanças:
- criação inicial só com informações gerais;
- construtor por etapas sem limite artificial;
- campos dinâmicos conforme tipo escolhido;
- slide exibido como apresentação (imagem dentro do slide);
- quiz e avaliação com várias perguntas por etapa;
- alternativas de múltipla escolha e seleção visual da correta pelo gestor;
- correção automática, nota mínima e indicação das respostas corretas quando reprovado;
- pontos somente após aprovação/conclusão válida;
- treinamento concluído pode ser reaberto em modo revisão, sem duplicar pontos;
- certificado permanece acessível no modo revisão;
- migration 0018 adiciona `questoes` em EtapaTreinamento.

Validação local deste pacote: arquivos Python compilados com sucesso. O ambiente de geração não possui Django instalado, então `manage.py check` e `makemigrations --check` devem ser executados no Codespaces antes do commit.
