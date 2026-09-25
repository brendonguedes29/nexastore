from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from gestao.models import Tarefa, PlanoAcao, NaoConformidade, Auditoria, DocumentoGestao, TrilhaColaborador, Notificacao, AlertaEnviado, Colaborador
from lojas.email_service import enviar_email


def _usuarios_empresa(loja):
    usuarios=[]
    if loja.dono_id: usuarios.append(loja.dono)
    usuarios += [c.usuario for c in Colaborador.objects.filter(loja=loja,ativo=True).select_related('usuario')]
    return {u.id:u for u in usuarios if u and u.is_active}.values()


def _destinatarios(loja, responsavel=None):
    if responsavel and getattr(responsavel,'usuario_id',None): return [responsavel.usuario]
    return list(_usuarios_empresa(loja))


def _avisar(loja, usuario, chave, titulo, mensagem, link, email=True):
    if AlertaEnviado.objects.filter(loja=loja,usuario=usuario,chave=chave,canal='plataforma').exists(): return 0
    Notificacao.objects.create(loja=loja,usuario=usuario,titulo=titulo,mensagem=mensagem,link=link)
    AlertaEnviado.objects.create(loja=loja,usuario=usuario,chave=chave,canal='plataforma')
    if email and usuario.email:
        perfil=getattr(usuario,'perfil_colaborador',None)
        if not perfil or perfil.email_notificacoes:
            try:
                html=f'<h2>{titulo}</h2><p>{mensagem}</p><p>Acesse a Nexa Gestão para acompanhar.</p>'
                enviar_email(usuario.email,f'Nexa Gestão • {titulo}',html)
                AlertaEnviado.objects.get_or_create(loja=loja,usuario=usuario,chave=chave,canal='email')
            except Exception as exc:
                print('ERRO ALERTA EMAIL:',exc)
    return 1


def processar_alertas(loja=None, enviar_email_alerta=True):
    hoje=timezone.localdate(); total=0
    def tratar(qs, data_attr, titulo_prefixo, link, resp_attr=None):
        nonlocal total
        for obj in qs:
            data=getattr(obj,data_attr,None)
            if not data: continue
            dias=(data-hoje).days
            if dias not in (7,1,0) and dias>=0: continue
            estado='atrasado' if dias<0 else ('hoje' if dias==0 else f'{dias}d')
            titulo=f'{titulo_prefixo} • ' + ('atrasado' if dias<0 else ('vence hoje' if dias==0 else f'vence em {dias} dia(s)'))
            msg=f'{obj} — prazo {data.strftime("%d/%m/%Y")}.'
            resp=getattr(obj,resp_attr,None) if resp_attr else None
            for u in _destinatarios(obj.loja,resp):
                total += _avisar(obj.loja,u,f'{obj.__class__.__name__}:{obj.pk}:{estado}',titulo,msg,link,enviar_email_alerta)
    lojas=[loja] if loja else None
    f={} if not lojas else {'loja__in':lojas}
    tratar(Tarefa.objects.filter(**f).exclude(status='concluida'),'fim','Tarefa',reverse('gestao_tarefas'),'responsavel')
    tratar(PlanoAcao.objects.filter(**f).exclude(status='concluido'),'quando','Plano de ação',reverse('gestao_planos'))
    tratar(NaoConformidade.objects.filter(**f).exclude(status='encerrada'),'prazo','Não conformidade',reverse('gestao_nc'))
    tratar(Auditoria.objects.filter(**f).exclude(status='concluida'),'data','Auditoria',reverse('gestao_auditorias'))
    tratar(DocumentoGestao.objects.filter(**f),'proxima_revisao','Revisão documental',reverse('gestao_documentos'))
    tratar(TrilhaColaborador.objects.filter(**f).exclude(status='concluido'),'prazo','Treinamento',reverse('portal_colaborador'),'colaborador')
    return total
