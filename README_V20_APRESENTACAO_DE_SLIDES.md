# V20 — Apresentação de slides real

- Uma etapa do tipo Slide agora contém vários slides internos.
- Cada slide possui título, texto e imagem opcional próprios.
- O gestor pode adicionar, remover e reordenar slides sem limite artificial.
- A prévia do editor atualiza título, texto e imagem localmente.
- O colaborador navega pela apresentação com Anterior/Próximo e contador interno.
- A etapa só é concluída pelo botão normal após a apresentação; pontos continuam vinculados à conclusão da etapa.
- Slides antigos continuam compatíveis por fallback para título/descrição/imagem legados.

Nova migration: `0019_etapatreinamento_slides.py`.
