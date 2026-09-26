from django.db.models import Sum

NIVEIS = [
    (1, 'Iniciante', 0),
    (2, 'Aprendiz', 500),
    (3, 'Praticante', 1200),
    (4, 'Especialista', 2200),
    (5, 'Referência', 3600),
    (6, 'Mestre', 5500),
    (7, 'Elite', 8000),
]

def nivel_por_pontos(pontos):
    atual=NIVEIS[0]
    for item in NIVEIS:
        if pontos >= item[2]: atual=item
        else: break
    return atual

def progresso_nivel(pontos):
    atual=nivel_por_pontos(pontos)
    idx=NIVEIS.index(atual)
    proximo=NIVEIS[idx+1] if idx+1 < len(NIVEIS) else None
    if not proximo:
        return {'numero':atual[0],'nome':atual[1],'inicio':atual[2],'proximo':None,'faltam':0,'percentual':100}
    faixa=max(1,proximo[2]-atual[2]); feito=max(0,pontos-atual[2])
    return {'numero':atual[0],'nome':atual[1],'inicio':atual[2],'proximo':proximo,'faltam':max(0,proximo[2]-pontos),'percentual':min(100,round(feito/faixa*100))}

def sincronizar_nivel(perfil):
    numero=nivel_por_pontos(perfil.pontos)[0]
    if perfil.nivel != numero:
        perfil.nivel=numero; perfil.save(update_fields=['nivel'])
    return numero

def conceder_pontos(perfil, categoria, ferramenta, titulo, pontos, detalhes=None, unico=True):
    from gestao.models import PontuacaoAtividade
    if not perfil or pontos <= 0: return 0
    qs=PontuacaoAtividade.objects.filter(loja=perfil.loja,colaborador=perfil,categoria=categoria,ferramenta=ferramenta,titulo=titulo)
    if unico and qs.exists(): return 0
    PontuacaoAtividade.objects.create(loja=perfil.loja,colaborador=perfil,categoria=categoria,ferramenta=ferramenta,titulo=titulo,pontos=pontos,detalhes=detalhes or {})
    perfil.pontos += pontos
    perfil.nivel=nivel_por_pontos(perfil.pontos)[0]
    perfil.save(update_fields=['pontos','nivel'])
    return pontos
