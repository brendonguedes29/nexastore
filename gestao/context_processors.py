def nexa_global(request):
    if not getattr(request,'user',None) or not request.user.is_authenticated:
        return {}
    try:
        from .models import Notificacao
        if hasattr(request.user,'perfil_colaborador'):
            loja=request.user.perfil_colaborador.loja
        elif hasattr(request.user,'loja'):
            loja=request.user.loja
        else:
            return {}
        return {'nexa_notificacoes_novas':Notificacao.objects.filter(loja=loja,usuario=request.user,lida=False).count()}
    except Exception:
        return {}
