from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.utils import timezone
from .models import *
from .forms import *


def _empresa(request): return request.user.loja

def _licenca(request, loja):
    loja.verificar_licenca()
    return loja.status_licenca in ['pendente','vencida'] or not loja.ativa

@login_required
def dashboard(request):
    loja=_empresa(request)
    if _licenca(request,loja): return redirect('licenca_bloqueada')
    indicadores=Indicador.objects.filter(loja=loja,ativo=True)[:6]
    dados={
      'loja':loja,'processos':Processo.objects.filter(loja=loja).count(),
      'ncs_abertas':NaoConformidade.objects.filter(loja=loja).exclude(status='encerrada').count(),
      'acoes_abertas':PlanoAcao.objects.filter(loja=loja).exclude(status='concluido').count(),
      'docs':DocumentoGestao.objects.filter(loja=loja).count(),'indicadores':indicadores,
      'auditorias':Auditoria.objects.filter(loja=loja).order_by('data')[:4],
      'acoes':PlanoAcao.objects.filter(loja=loja).exclude(status='concluido').order_by('quando')[:5],
      'iso_total':RequisitoISO.objects.filter(loja=loja).count(),
      'iso_conforme':RequisitoISO.objects.filter(loja=loja,status='conforme').count(),
    }
    return render(request,'gestao/dashboard.html',dados)

def _crud(request, model, formcls, titulo, template='gestao/lista_form.html'):
    loja=_empresa(request); qs=model.objects.filter(loja=loja).order_by('-id')
    obj=None
    if request.GET.get('editar'): obj=get_object_or_404(qs,pk=request.GET['editar'])
    form=formcls(request.POST or None, request.FILES or None, instance=obj)
    # restringe FKs à empresa
    for nome in ('processo','indicador'):
        if nome in form.fields:
            mdl=Processo if nome=='processo' else Indicador
            form.fields[nome].queryset=mdl.objects.filter(loja=loja)
    if request.method=='POST' and form.is_valid():
        item=form.save(commit=False); item.loja=loja; item.save(); return redirect(request.path)
    return render(request,template,{'loja':loja,'itens':qs,'form':form,'titulo':titulo})

@login_required
def processos(request): return _crud(request,Processo,ProcessoForm,'Mapeamento de Processos')
@login_required
def indicadores(request): return _crud(request,Indicador,IndicadorForm,'Indicadores e Metas')
@login_required
def planos(request): return _crud(request,PlanoAcao,PlanoAcaoForm,'Planos de Ação • 5W2H')
@login_required
def nao_conformidades(request): return _crud(request,NaoConformidade,NCForm,'Não Conformidades e CAPA')
@login_required
def documentos(request): return _crud(request,DocumentoGestao,DocumentoForm,'Gestão Documental')
@login_required
def auditorias(request): return _crud(request,Auditoria,AuditoriaForm,'Auditorias')
@login_required
def iso(request): return _crud(request,RequisitoISO,ISOForm,'ISO 9001 • Implantação e Evidências')
@login_required
def fmea(request): return _crud(request,RiscoFMEA,FMEAForm,'FMEA • Riscos de Processo')
@login_required
def producao(request): return _crud(request,RegistroProducao,ProducaoForm,'Produção e OEE')

@login_required
def ferramentas(request):
    return render(request,'gestao/ferramentas.html',{'loja':_empresa(request)})

@login_required
def academia(request):
    return render(request,'gestao/academia.html',{'loja':_empresa(request)})

def portal_empresa(request):
    loja=getattr(request,'loja',None)
    if not loja: return redirect('root_view')
    loja.verificar_licenca()
    if not loja.ativa: return render(request,'gestao/portal_indisponivel.html',{'loja':loja},status=403)
    indicadores=Indicador.objects.filter(loja=loja,ativo=True)[:6]
    docs=DocumentoGestao.objects.filter(loja=loja,aprovado=True)[:8]
    if request.method=='POST':
        # honeypot simples contra bots
        if not request.POST.get('website'):
            titulo=request.POST.get('titulo','').strip()[:180]; descricao=request.POST.get('descricao','').strip()[:2000]
            if titulo and descricao:
                IdeiaMelhoria.objects.create(loja=loja,titulo=titulo,descricao=descricao,autor=request.POST.get('autor','')[:120])
        return redirect('/')
    return render(request,'gestao/portal_empresa.html',{'loja':loja,'indicadores':indicadores,'documentos':docs})
