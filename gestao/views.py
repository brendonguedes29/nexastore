from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from functools import wraps
import hashlib
from .models import *
from .forms import *


def _empresa(request):
    if hasattr(request.user,'perfil_colaborador'): return request.user.perfil_colaborador.loja
    return request.user.loja

def _licenca_ativa(loja):
    loja.verificar_licenca(); return bool(loja.ativa and loja.status_licenca not in ['pendente','vencida'])

def plano_ativo(view):
    @wraps(view)
    @login_required
    def inner(request,*a,**kw):
        loja=_empresa(request)
        if not _licenca_ativa(loja):
            messages.warning(request,'Este recurso é liberado após a ativação do plano da empresa.')
            return redirect('gestao_dashboard')
        return view(request,*a,**kw)
    return inner

@login_required
def dashboard(request):
    loja=_empresa(request); ativa=_licenca_ativa(loja)
    dados={'loja':loja,'licenca_ativa':ativa,'processos':Processo.objects.filter(loja=loja).count(),'ncs_abertas':NaoConformidade.objects.filter(loja=loja).exclude(status='encerrada').count(),'acoes_abertas':PlanoAcao.objects.filter(loja=loja).exclude(status='concluido').count(),'tarefas':Tarefa.objects.filter(loja=loja).exclude(status='concluida').count(),'colaboradores':Colaborador.objects.filter(loja=loja,ativo=True).count(),'indicadores':Indicador.objects.filter(loja=loja,ativo=True)[:6],'acoes':PlanoAcao.objects.filter(loja=loja).exclude(status='concluido').order_by('quando')[:5],'notas':NotaWorkspace.objects.filter(loja=loja).order_by('-fixada','-id')[:6]}
    return render(request,'gestao/dashboard.html',dados)

def _crud(request, model, formcls, titulo, template='gestao/lista_form.html'):
    loja=_empresa(request); qs=model.objects.filter(loja=loja).order_by('-id'); obj=None
    if request.GET.get('editar'): obj=get_object_or_404(qs,pk=request.GET['editar'])
    form=formcls(request.POST or None,request.FILES or None,instance=obj)
    maps={'processo':Processo,'indicador':Indicador,'setor':Setor,'responsavel':Colaborador,'colaborador':Colaborador,'treinamento':Treinamento}
    for nome,mdl in maps.items():
        if nome in form.fields: form.fields[nome].queryset=mdl.objects.filter(loja=loja)
    if request.method=='POST' and form.is_valid():
        item=form.save(commit=False); item.loja=loja
        if hasattr(item,'autor_id') and not item.autor_id: item.autor=request.user
        item.save(); messages.success(request,'Registro salvo com sucesso.'); return redirect(request.path)
    return render(request,template,{'loja':loja,'itens':qs,'form':form,'titulo':titulo})

@plano_ativo
def processos(request): return _crud(request,Processo,ProcessoForm,'Mapeamento de Processos')
@plano_ativo
def indicadores(request): return _crud(request,Indicador,IndicadorForm,'Indicadores e Metas')
@plano_ativo
def planos(request): return _crud(request,PlanoAcao,PlanoAcaoForm,'Planos de Ação • 5W2H')
@plano_ativo
def nao_conformidades(request): return _crud(request,NaoConformidade,NCForm,'Não Conformidades e CAPA')
@plano_ativo
def documentos(request): return _crud(request,DocumentoGestao,DocumentoForm,'Gestão Documental')
@plano_ativo
def auditorias(request): return _crud(request,Auditoria,AuditoriaForm,'Auditorias')
@plano_ativo
def iso(request): return _crud(request,RequisitoISO,ISOForm,'ISO 9001 • Implantação e Evidências')
@plano_ativo
def fmea(request): return _crud(request,RiscoFMEA,FMEAForm,'FMEA • Riscos de Processo')
@plano_ativo
def producao(request): return _crud(request,RegistroProducao,ProducaoForm,'Produção e OEE')
@plano_ativo
def setores(request): return _crud(request,Setor,SetorForm,'Setores e Áreas')
@plano_ativo
def tarefas(request): return _crud(request,Tarefa,TarefaForm,'Tarefas e Projetos','gestao/tarefas.html')
@plano_ativo
def treinamentos(request): return _crud(request,Treinamento,TreinamentoForm,'Treinamentos')

@plano_ativo
def workspace(request):
    loja=_empresa(request); form=NotaForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        n=form.save(commit=False); n.loja=loja; n.autor=request.user; n.save(); return redirect('gestao_workspace')
    return render(request,'gestao/workspace.html',{'loja':loja,'form':form,'notas':NotaWorkspace.objects.filter(loja=loja).order_by('-fixada','-id')})

@plano_ativo
def ferramentas(request):
    loja=_empresa(request)
    if request.method=='POST':
        ferramenta=request.POST.get('ferramenta'); titulo=request.POST.get('titulo','').strip(); problema=request.POST.get('problema','').strip()
        campos={k:v for k,v in request.POST.items() if k not in ['csrfmiddlewaretoken','ferramenta','titulo','problema'] and v.strip()}
        if ferramenta and titulo:
            ProjetoQualidade.objects.create(loja=loja,ferramenta=ferramenta,titulo=titulo,problema=problema,responsavel=request.user.get_full_name() or request.user.username,dados=campos,status='andamento')
            messages.success(request,'Ferramenta salva. Você pode continuar a melhoria depois.')
            return redirect('gestao_ferramentas')
    return render(request,'gestao/ferramentas.html',{'loja':loja,'projetos':ProjetoQualidade.objects.filter(loja=loja).order_by('-id')[:12]})

@plano_ativo
def colaboradores(request):
    loja=_empresa(request)
    if request.method=='POST':
        nome=request.POST.get('nome','').strip(); email=request.POST.get('email','').strip().lower(); senha=request.POST.get('senha','').strip(); setor_id=request.POST.get('setor')
        if nome and email and senha and not User.objects.filter(username=email).exists():
            u=User.objects.create_user(username=email,email=email,password=senha,first_name=nome,is_active=True)
            Colaborador.objects.create(loja=loja,usuario=u,setor_id=setor_id or None,cargo=request.POST.get('cargo',''))
            messages.success(request,'Colaborador criado. Ele já pode acessar o Portal do Colaborador.')
        else: messages.error(request,'Preencha os campos ou use outro e-mail.')
        return redirect('gestao_colaboradores')
    return render(request,'gestao/colaboradores.html',{'loja':loja,'colaboradores':Colaborador.objects.filter(loja=loja).select_related('usuario','setor'),'setores':Setor.objects.filter(loja=loja)})

@plano_ativo
def academia(request):
    loja=_empresa(request); perfil=getattr(request.user,'perfil_colaborador',None)
    return render(request,'gestao/academia.html',{'loja':loja,'perfil':perfil,'tentativas':TentativaJogo.objects.filter(loja=loja,colaborador=perfil).order_by('-id')[:10] if perfil else []})

@plano_ativo
def jogo_phishing(request):
    loja=_empresa(request); perfil=getattr(request.user,'perfil_colaborador',None)
    questoes=[
      {'id':'q1','texto':'E-mail do “Financeiro” pede sua senha para evitar bloqueio em 30 minutos.','correta':'phishing','dica':'Senha + urgência artificial são sinais fortes de fraude.'},
      {'id':'q2','texto':'Aviso interno conhecido, sem link, orienta abrir o sistema pelo favorito corporativo.','correta':'legitimo','dica':'A mensagem não pede credenciais nem induz clique inesperado.'},
      {'id':'q3','texto':'Mensagem de fornecedor informa nova conta bancária e exige pagamento imediato por um link encurtado.','correta':'phishing','dica':'Mudança financeira deve ser validada por segundo canal.'},
      {'id':'q4','texto':'RH pede atualização cadastral no portal corporativo acessado pelo endereço habitual da empresa.','correta':'legitimo','dica':'O canal conhecido reduz o risco; ainda assim confira domínio e HTTPS.'},
      {'id':'q5','texto':'“Microsoft Suporte” envia anexo inesperado para “revalidar sua caixa postal”.','correta':'phishing','dica':'Anexo inesperado e pedido de revalidação são sinais de alerta.'},
    ]
    resultado=None
    if request.method=='POST':
        acertos=sum(1 for q in questoes if request.POST.get(q['id'])==q['correta']); pontos=acertos*20; resultado={'acertos':acertos,'total':len(questoes),'pontos':pontos}
        if perfil:
            TentativaJogo.objects.create(loja=loja,colaborador=perfil,jogo='phishing',pontuacao=pontos,total=100,detalhes={'acertos':acertos}); PontuacaoAtividade.objects.create(loja=loja,colaborador=perfil,categoria='jogo',ferramenta='phishing',titulo='Simulação Phishing ou legítimo?',pontos=pontos,detalhes={'acertos':acertos,'total':len(questoes)}); perfil.pontos+=pontos; perfil.nivel=1+(perfil.pontos//500); perfil.save(update_fields=['pontos','nivel']);
            if acertos==len(questoes): ConquistaColaborador.objects.get_or_create(loja=loja,colaborador=perfil,codigo='phishing_perfeito',defaults={'titulo':'Radar Antiphishing','descricao':'Acertou 100% em uma simulação de phishing.'})
    return render(request,'gestao/jogo_phishing.html',{'loja':loja,'questoes':questoes,'resultado':resultado})

@plano_ativo
def lgpd(request):
    loja=_empresa(request); form=LGPDForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        r=form.save(commit=False); r.loja=loja; r.usuario=request.user; ip=request.META.get('REMOTE_ADDR',''); r.ip_hash=hashlib.sha256(ip.encode()).hexdigest() if ip else ''; r.save(); messages.success(request,'Registro LGPD documentado.'); return redirect('gestao_lgpd')
    return render(request,'gestao/lgpd.html',{'loja':loja,'form':form,'registros':RegistroLGPD.objects.filter(loja=loja).order_by('-registrado_em')[:30]})

@login_required
def portal_colaborador(request):
    perfil=getattr(request.user,'perfil_colaborador',None)
    if not perfil: return redirect('gestao_dashboard')
    loja=perfil.loja
    return render(request,'gestao/portal_colaborador.html',{'loja':loja,'perfil':perfil,'tarefas':Tarefa.objects.filter(loja=loja,responsavel=perfil).exclude(status='concluida'),'trilhas':TrilhaColaborador.objects.filter(loja=loja,colaborador=perfil).select_related('treinamento'),'conquistas':ConquistaColaborador.objects.filter(loja=loja,colaborador=perfil).order_by('-concedida_em')})

def portal_empresa(request):
    loja=getattr(request,'loja',None)
    if not loja:return redirect('root_view')
    loja.verificar_licenca()
    if not loja.ativa:return render(request,'gestao/portal_indisponivel.html',{'loja':loja},status=403)
    return render(request,'gestao/portal_empresa.html',{'loja':loja,'indicadores':Indicador.objects.filter(loja=loja,ativo=True)[:6],'documentos':DocumentoGestao.objects.filter(loja=loja,aprovado=True)[:8]})

@plano_ativo
def tarefa_status(request):
    if request.method!='POST': return redirect('gestao_tarefas')
    loja=_empresa(request); t=get_object_or_404(Tarefa,loja=loja,pk=request.POST.get('id'))
    status=request.POST.get('status')
    if status in dict(Tarefa.STATUS): t.status=status; t.save(update_fields=['status','atualizado_em'])
    return redirect('gestao_tarefas')

@plano_ativo
def lgpd_inventario(request): return _crud(request,AtividadeTratamento,AtividadeTratamentoForm,'LGPD • Inventário de Tratamentos')
@plano_ativo
def lgpd_titulares(request):
    loja=_empresa(request); form=SolicitacaoTitularForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        o=form.save(commit=False); o.loja=loja; o.save(); o.protocolo=f'DSR-{o.id:06d}'; o.save(update_fields=['protocolo']); messages.success(request,'Solicitação registrada com protocolo.'); return redirect('gestao_lgpd_titulares')
    return render(request,'gestao/lista_form.html',{'loja':loja,'itens':SolicitacaoTitular.objects.filter(loja=loja).order_by('-id'),'form':form,'titulo':'LGPD • Direitos dos Titulares'})
@plano_ativo
def lgpd_incidentes(request): return _crud(request,IncidentePrivacidade,IncidentePrivacidadeForm,'LGPD • Incidentes de Privacidade')


@login_required
def meu_perfil(request):
    perfil=getattr(request.user,'perfil_colaborador',None)
    if not perfil: return redirect('gestao_dashboard')
    form=PerfilColaboradorForm(request.POST or None,request.FILES or None,instance=perfil)
    if request.method=='POST' and form.is_valid(): form.save(); messages.success(request,'Perfil atualizado.'); return redirect('gestao_meu_perfil')
    historico=PontuacaoAtividade.objects.filter(loja=perfil.loja,colaborador=perfil).order_by('-criado_em')[:20]
    conquistas=ConquistaColaborador.objects.filter(loja=perfil.loja,colaborador=perfil).order_by('-concedida_em')
    return render(request,'gestao/perfil.html',{'loja':perfil.loja,'perfil':perfil,'form':form,'historico':historico,'conquistas':conquistas})

@login_required
def perfil_publico(request,pk):
    meu=getattr(request.user,'perfil_colaborador',None); loja=meu.loja if meu else _empresa(request)
    perfil=get_object_or_404(Colaborador,pk=pk,loja=loja,ativo=True)
    if not perfil.perfil_visivel and perfil.usuario_id!=request.user.id: return redirect('gestao_ranking')
    return render(request,'gestao/perfil_publico.html',{'loja':loja,'perfil':perfil,'conquistas':ConquistaColaborador.objects.filter(loja=loja,colaborador=perfil) if perfil.mostrar_conquistas else []})

@login_required
def ranking(request):
    perfil=getattr(request.user,'perfil_colaborador',None); loja=perfil.loja if perfil else _empresa(request)
    pessoas=Colaborador.objects.filter(loja=loja,ativo=True,ranking_visivel=True).select_related('usuario','setor').order_by('-pontos','usuario__first_name')
    ferramenta=request.GET.get('ferramenta','')
    ranking_ferramenta=[]
    if ferramenta:
        from django.db.models import Sum
        ranking_ferramenta=PontuacaoAtividade.objects.filter(loja=loja,ferramenta=ferramenta,colaborador__ranking_visivel=True).values('colaborador','colaborador__usuario__first_name','colaborador__usuario__username').annotate(total=Sum('pontos')).order_by('-total')[:50]
    ferramentas=PontuacaoAtividade.objects.filter(loja=loja).exclude(ferramenta='').values_list('ferramenta',flat=True).distinct()
    return render(request,'gestao/ranking.html',{'loja':loja,'pessoas':pessoas,'perfil':perfil,'ferramentas':ferramentas,'ferramenta':ferramenta,'ranking_ferramenta':ranking_ferramenta})

@plano_ativo
def reconhecimentos(request):
    loja=_empresa(request); form=ReconhecimentoForm(request.POST or None)
    form.fields['colaborador'].queryset=Colaborador.objects.filter(loja=loja,ativo=True)
    if request.method=='POST' and form.is_valid():
        r=form.save(commit=False); r.loja=loja; r.concedido_por=request.user; r.save(); c=r.colaborador; c.pontos+=r.pontos; c.nivel=1+(c.pontos//500); c.save(update_fields=['pontos','nivel']); PontuacaoAtividade.objects.create(loja=loja,colaborador=c,categoria='reconhecimento',ferramenta='reconhecimento',titulo=r.titulo,pontos=r.pontos); messages.success(request,'Reconhecimento concedido.'); return redirect('gestao_reconhecimentos')
    return render(request,'gestao/reconhecimentos.html',{'loja':loja,'form':form,'itens':Reconhecimento.objects.filter(loja=loja).select_related('colaborador__usuario').order_by('-criado_em')[:30]})

@login_required
def notificacoes(request):
    perfil=getattr(request.user,'perfil_colaborador',None); loja=perfil.loja if perfil else _empresa(request)
    itens=Notificacao.objects.filter(loja=loja,usuario=request.user)[:50]
    if request.method=='POST':
        itens.update(lida=True); return redirect('gestao_notificacoes')
    return render(request,'gestao/notificacoes.html',{'loja':loja,'itens':itens})

@plano_ativo
def comentar_tarefa(request,pk):
    loja=_empresa(request); tarefa=get_object_or_404(Tarefa,pk=pk,loja=loja)
    if request.method=='POST' and request.POST.get('texto','').strip():
        ComentarioTarefa.objects.create(loja=loja,tarefa=tarefa,autor=request.user,texto=request.POST['texto'].strip())
        RegistroAuditoriaSistema.objects.create(loja=loja,usuario=request.user,acao='comentario',objeto=f'Tarefa #{tarefa.id}',descricao='Comentário adicionado à tarefa.')
        if tarefa.responsavel and tarefa.responsavel.usuario_id!=request.user.id:
            Notificacao.objects.create(loja=loja,usuario=tarefa.responsavel.usuario,titulo='Novo comentário em tarefa',mensagem=tarefa.titulo,link='/gestao/tarefas/')
    return redirect('gestao_tarefas')

@plano_ativo
def auditoria_sistema(request):
    loja=_empresa(request)
    return render(request,'gestao/auditoria_sistema.html',{'loja':loja,'itens':RegistroAuditoriaSistema.objects.filter(loja=loja).select_related('usuario')[:100]})

@plano_ativo
def metas_equipe(request):
    return _crud(request,MetaEquipe,MetaEquipeForm,'Metas & Desafios de Equipe')

def _premiar_jogo(loja,perfil,jogo,titulo,pontos,total,detalhes):
    if not perfil:return
    TentativaJogo.objects.create(loja=loja,colaborador=perfil,jogo=jogo,pontuacao=pontos,total=total,detalhes=detalhes)
    PontuacaoAtividade.objects.create(loja=loja,colaborador=perfil,categoria='jogo',ferramenta=jogo,titulo=titulo,pontos=pontos,detalhes=detalhes)
    perfil.pontos+=pontos; perfil.nivel=1+(perfil.pontos//500); perfil.save(update_fields=['pontos','nivel'])

@plano_ativo
def jogo_lean(request):
    loja=_empresa(request); perfil=getattr(request.user,'perfil_colaborador',None)
    questoes=[('q1','Produzir antes da demanda real','superproducao'),('q2','Operador aguardando liberação da máquina','espera'),('q3','Levar material várias vezes entre prédios','transporte'),('q4','Refazer uma peça fora de especificação','defeitos'),('q5','Funcionário treinado sem autonomia para sugerir melhorias','talento')]
    opcoes=[('superproducao','Superprodução'),('espera','Espera'),('transporte','Transporte'),('defeitos','Defeitos'),('talento','Talento não aproveitado')]; resultado=None
    if request.method=='POST':
        acertos=sum(request.POST.get(q)==c for q,_,c in questoes); pontos=acertos*20; resultado={'acertos':acertos,'total':len(questoes),'pontos':pontos}; _premiar_jogo(loja,perfil,'lean','Caça ao desperdício',pontos,100,resultado)
        if perfil and acertos==len(questoes): ConquistaColaborador.objects.get_or_create(loja=loja,colaborador=perfil,codigo='lean_perfeito',defaults={'titulo':'Olhar Lean','descricao':'Identificou todos os desperdícios do desafio.'})
    return render(request,'gestao/jogo_lean.html',{'loja':loja,'questoes':questoes,'opcoes':opcoes,'resultado':resultado})

@plano_ativo
def jogo_causa_raiz(request):
    loja=_empresa(request); perfil=getattr(request.user,'perfil_colaborador',None); resultado=None
    etapas=[('q1','Máquina parou durante o turno. Qual primeira pergunta é mais útil?',['Quem é culpado?','Por que a máquina parou?','Quanto custa uma nova?'],1),('q2','Parou porque superaqueceu. Próximo passo?',['Por que superaqueceu?','Reiniciar e esquecer','Trocar o operador'],0),('q3','Superaqueceu por falta de lubrificação. O que investigar?',['Por que a lubrificação não ocorreu?','Comprar outra máquina','Encerrar análise'],0),('q4','A rotina não foi executada. Melhor conclusão?',['Registrar culpado','Investigar por que o processo permitiu a falha','Punir a equipe'],1)]
    if request.method=='POST':
        acertos=sum(str(c)==request.POST.get(q) for q,_,_,c in etapas); pontos=acertos*25; resultado={'acertos':acertos,'total':len(etapas),'pontos':pontos}; _premiar_jogo(loja,perfil,'causa_raiz','Detetive da causa raiz',pontos,100,resultado)
        if perfil and acertos==len(etapas): ConquistaColaborador.objects.get_or_create(loja=loja,colaborador=perfil,codigo='detetive_causa',defaults={'titulo':'Detetive da Causa Raiz','descricao':'Conduziu uma investigação sem atalhos ou culpabilização.'})
    return render(request,'gestao/jogo_causa_raiz.html',{'loja':loja,'etapas':etapas,'resultado':resultado})
