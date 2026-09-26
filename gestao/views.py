from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings
from lojas.email_service import enviar_email
from functools import wraps
import hashlib
import uuid
from datetime import timedelta
from django.db.models import Max
from django.db.models import Q
from django.http import JsonResponse
from .services.alertas import processar_alertas
from .services.pontos import progresso_nivel, conceder_pontos, sincronizar_nivel
from .models import *
from .forms import *


def _empresa(request):
    if hasattr(request.user,'perfil_colaborador'): return request.user.perfil_colaborador.loja
    return request.user.loja

def _data_post(request, nome):
    valor=request.POST.get(nome,'').strip()
    return parse_date(valor) if valor else None

def _fk_empresa(model, loja, valor):
    if not valor: return None
    try: return model.objects.filter(loja=loja,pk=valor).first()
    except (TypeError, ValueError): return None

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
    if hasattr(request.user,'perfil_colaborador') and request.user.perfil_colaborador.papel!='gestor_empresa': return redirect('portal_colaborador')
    try: processar_alertas(loja,enviar_email_alerta=False)
    except Exception as exc: print('ALERTAS DASHBOARD:',exc)
    hoje=timezone.localdate(); limite=hoje+timedelta(days=7)
    equipe=Colaborador.objects.filter(loja=loja,ativo=True).select_related('usuario','setor')[:8]
    proximos=Tarefa.objects.filter(loja=loja,fim__isnull=False,fim__lte=limite).exclude(status='concluida').select_related('responsavel__usuario').order_by('fim')[:8]
    dados={'loja':loja,'licenca_ativa':ativa,'processos':Processo.objects.filter(loja=loja).count(),'ncs_abertas':NaoConformidade.objects.filter(loja=loja).exclude(status='encerrada').count(),'acoes_abertas':PlanoAcao.objects.filter(loja=loja).exclude(status='concluido').count(),'tarefas':Tarefa.objects.filter(loja=loja).exclude(status='concluida').count(),'colaboradores':Colaborador.objects.filter(loja=loja,ativo=True).count(),'setores':Setor.objects.filter(loja=loja,ativo=True).count(),'indicadores':Indicador.objects.filter(loja=loja,ativo=True)[:6],'acoes':PlanoAcao.objects.filter(loja=loja).exclude(status='concluido').order_by('quando')[:5],'notas':NotaWorkspace.objects.filter(loja=loja).order_by('-fixada','-id')[:6],'equipe':equipe,'proximos':proximos,'notificacoes_novas':Notificacao.objects.filter(loja=loja,usuario=request.user,lida=False).count(),'atividades_recentes':RegistroAuditoriaSistema.objects.filter(loja=loja).select_related('usuario').order_by('-criado_em')[:12],'analises_recentes':ProjetoQualidade.objects.filter(loja=loja).select_related('processo','setor').order_by('-criado_em')[:8],'today':hoje}
    return render(request,'gestao/dashboard.html',dados)

def _crud(request, model, formcls, titulo, template='gestao/lista_form.html'):
    perfil=getattr(request.user,'perfil_colaborador',None)
    if perfil and perfil.papel!='gestor_empresa':
        messages.warning(request,'Este recurso é gerencial. No seu portal você encontra apenas itens atribuídos ao seu perfil.')
        return redirect('portal_colaborador')
    loja=_empresa(request); qs=model.objects.filter(loja=loja).order_by('-id'); obj=None
    if request.GET.get('editar'): obj=get_object_or_404(qs,pk=request.GET['editar'])
    form=formcls(request.POST or None,request.FILES or None,instance=obj)
    maps={'processo':Processo,'indicador':Indicador,'setor':Setor,'responsavel':Colaborador,'responsavel_colaborador':Colaborador,'colaborador':Colaborador,'treinamento':Treinamento}
    for nome,mdl in maps.items():
        if nome in form.fields: form.fields[nome].queryset=mdl.objects.filter(loja=loja)
    if request.method=='POST' and form.is_valid():
        item=form.save(commit=False); item.loja=loja
        if hasattr(item,'autor_id') and not item.autor_id: item.autor=request.user
        item.save()
        RegistroAuditoriaSistema.objects.create(loja=loja,usuario=request.user,acao='registro_salvo',objeto=f'{titulo} #{item.pk}',descricao=f'{str(item)} foi salvo/atualizado.')
        perfil=getattr(request.user,'perfil_colaborador',None)
        status=getattr(item,'status','')
        conclusivos=('concluido','concluida','encerrada','conforme','implantada')
        if perfil and status in conclusivos:
            chave=f'{model.__name__} concluído #{item.pk}'
            if not PontuacaoAtividade.objects.filter(loja=loja,colaborador=perfil,titulo=chave).exists():
                PontuacaoAtividade.objects.create(loja=loja,colaborador=perfil,categoria='qualidade',ferramenta=model.__name__.lower(),titulo=chave,pontos=25)
                perfil.pontos+=25; perfil.nivel=1+(perfil.pontos//500); perfil.save(update_fields=['pontos','nivel'])
        messages.success(request,'Registro salvo com sucesso.'); return redirect(request.path)
    registros=[]
    hoje=timezone.localdate()
    for item in qs[:60]:
        titulo_item=getattr(item,'titulo',None) or getattr(item,'nome',None) or str(item)
        inicio=getattr(item,'inicio',None) or getattr(item,'data',None) or (getattr(item,'criado_em',None).date() if getattr(item,'criado_em',None) else None)
        previsao=getattr(item,'previsao_conclusao',None) or getattr(item,'fim',None) or getattr(item,'prazo',None) or getattr(item,'quando',None) or getattr(item,'proxima_revisao',None)
        conclusao=getattr(item,'concluido_em',None)
        if hasattr(conclusao,'date'): conclusao=conclusao.date()
        status=getattr(item,'status',None)
        if status and hasattr(item,'get_status_display'): status_label=item.get_status_display()
        elif hasattr(item,'ativo'): status_label='Ativo' if item.ativo else 'Inativo'
        else: status_label='Registrado'
        prazo_classe='neutral'
        if conclusao: prazo_classe='done'
        elif previsao:
            if previsao < hoje: prazo_classe='late'
            elif previsao <= hoje+timedelta(days=7): prazo_classe='soon'
        responsavel=getattr(item,'responsavel',None) or getattr(item,'quem',None) or getattr(item,'auditor',None) or ''
        registros.append({'id':item.pk,'titulo':titulo_item,'tipo':titulo,'inicio':inicio,'previsao':previsao,'conclusao':conclusao,'status':status_label,'prazo_classe':prazo_classe,'responsavel':responsavel,'criado_em':getattr(item,'criado_em',None)})
    return render(request,template,{'loja':loja,'itens':qs,'registros_detalhes':registros,'form':form,'titulo':titulo})

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
def iso(request):
    loja=_empresa(request)
    roteiro=[
      ('4','Contexto da organização','Mapeie contexto interno e externo, partes interessadas, escopo do SGQ e processos necessários.'),
      ('5','Liderança','Defina responsabilidades, política da qualidade, compromisso da liderança e fortalecimento da cultura da qualidade.'),
      ('6','Planejamento','Trate riscos e oportunidades separadamente, estabeleça objetivos da qualidade e planeje mudanças.'),
      ('7','Suporte','Estruture recursos, competências, conscientização, comunicação, conhecimento organizacional e informação documentada.'),
      ('8','Operação','Planeje e controle a operação, requisitos de clientes, fornecedores externos, produção/serviço e tratamento de saídas não conformes.'),
      ('9','Avaliação de desempenho','Defina monitoramento, indicadores, análise de dados, auditorias internas e análise crítica pela direção.'),
      ('10','Melhoria','Registre não conformidades, ações corretivas, verificação de eficácia e melhoria contínua do SGQ.'),
    ]
    for clausula,titulo,orientacao in roteiro:
        RequisitoISO.objects.get_or_create(loja=loja,norma='ISO 9001:2026',clausula=clausula,defaults={'titulo':titulo,'orientacao':orientacao})
    return _crud(request,RequisitoISO,ISOForm,'ISO 9001:2026 • Jornada de implantação','gestao/iso.html')
@plano_ativo
def fmea(request): return _crud(request,RiscoFMEA,FMEAForm,'FMEA de Processo • Modos de falha e ações','gestao/fmea.html')
@plano_ativo
def producao(request): return _crud(request,RegistroProducao,ProducaoForm,'Produção e OEE','gestao/oee.html')
@plano_ativo
def setores(request): return _crud(request,Setor,SetorForm,'Setores e Áreas')
@plano_ativo
def tarefas(request): return _crud(request,Tarefa,TarefaForm,'Tarefas e Projetos','gestao/tarefas.html')
@plano_ativo
def treinamentos(request):
    perfil=getattr(request.user,'perfil_colaborador',None)
    if perfil and perfil.papel!='gestor_empresa': return redirect('portal_colaborador')
    loja=_empresa(request); form=TreinamentoForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        o=form.save(commit=False); o.loja=loja; o.save(); messages.success(request,'Treinamento criado. Agora monte as etapas da trilha.'); return redirect('gestao_treinamento_editar',pk=o.pk)
    return render(request,'gestao/treinamentos.html',{'loja':loja,'form':form,'itens':Treinamento.objects.filter(loja=loja).prefetch_related('etapas').order_by('-id')})

@plano_ativo
def treinamento_editar(request,pk):
    perfil=getattr(request.user,'perfil_colaborador',None)
    if perfil and perfil.papel!='gestor_empresa': return redirect('portal_colaborador')
    loja=_empresa(request); treinamento=get_object_or_404(Treinamento,loja=loja,pk=pk); form=EtapaTreinamentoForm(request.POST or None,request.FILES or None)
    if request.method=='POST' and form.is_valid():
        e=form.save(commit=False); e.loja=loja; e.treinamento=treinamento; e.save(); messages.success(request,'Etapa adicionada à trilha.'); return redirect('gestao_treinamento_editar',pk=pk)
    return render(request,'gestao/treinamento_editar.html',{'loja':loja,'treinamento':treinamento,'form':form,'etapas':treinamento.etapas.all(),'colaboradores':Colaborador.objects.filter(loja=loja,ativo=True)})

@plano_ativo
def treinamento_atribuir(request,pk):
    perfil=getattr(request.user,'perfil_colaborador',None)
    if perfil and perfil.papel!='gestor_empresa': return redirect('portal_colaborador')
    loja=_empresa(request); treinamento=get_object_or_404(Treinamento,loja=loja,pk=pk)
    if request.method=='POST':
        inicio=_data_post(request,'inicio'); prazo=_data_post(request,'prazo')
        ids=request.POST.getlist('colaboradores')
        for c in Colaborador.objects.filter(loja=loja,pk__in=ids):
            trilha,_=TrilhaColaborador.objects.get_or_create(loja=loja,colaborador=c,treinamento=treinamento)
            trilha.inicio=inicio; trilha.prazo=prazo; trilha.save(update_fields=['inicio','prazo'])
            Notificacao.objects.create(loja=loja,usuario=c.usuario,titulo='Novo treinamento atribuído',mensagem=treinamento.titulo,link=reverse('gestao_trilha_executar',args=[trilha.pk]))
        messages.success(request,'Treinamento atribuído à equipe.'); return redirect('gestao_treinamento_editar',pk=pk)
    return redirect('gestao_treinamento_editar',pk=pk)

@login_required
def trilha_executar(request,pk):
    perfil=getattr(request.user,'perfil_colaborador',None)
    if not perfil: return redirect('gestao_dashboard')
    trilha=get_object_or_404(TrilhaColaborador,pk=pk,colaborador=perfil,loja=perfil.loja); hoje=timezone.localdate()
    if trilha.inicio and hoje<trilha.inicio:
        messages.info(request,f'Este treinamento será liberado em {trilha.inicio.strftime("%d/%m/%Y")}.'); return redirect('portal_colaborador')
    etapas=list(trilha.treinamento.etapas.all()); atual=None
    for e in etapas:
        prog,_=ProgressoEtapa.objects.get_or_create(loja=perfil.loja,colaborador=perfil,etapa=e)
        if not prog.concluida: atual=e; break
    if request.method=='POST' and atual:
        resposta=request.POST.get('resposta','').strip(); prog=ProgressoEtapa.objects.get(loja=perfil.loja,colaborador=perfil,etapa=atual); prog.resposta=resposta; prog.concluida=True; prog.concluida_em=timezone.now(); prog.save()
        chave=f'{trilha.treinamento.titulo} • {atual.titulo}'
        if trilha.treinamento.origem!='nexa':
            ganhos=conceder_pontos(perfil,'treinamento','treinamento_empresa',chave,atual.pontos,{'origem':'empresa'},unico=True)
            if ganhos: Notificacao.objects.create(loja=perfil.loja,usuario=request.user,titulo=f'Parabéns! +{ganhos} ⭐ pontos',mensagem=f'Você ganhou {ganhos} pontos por concluir a etapa “{atual.titulo}” do treinamento {trilha.treinamento.titulo}.',link=reverse('portal_colaborador'))
        return redirect('gestao_trilha_executar',pk=pk)
    concluidas=ProgressoEtapa.objects.filter(loja=perfil.loja,colaborador=perfil,etapa__treinamento=trilha.treinamento,concluida=True).count()
    if etapas and concluidas>=len(etapas) and trilha.status!='concluido' and trilha.treinamento.origem=='nexa':
        return redirect('gestao_treinamento_nexa_avaliacao',pk=trilha.pk)
    if etapas and concluidas>=len(etapas) and trilha.status!='concluido':
        trilha.status='concluido'; trilha.concluido_em=timezone.now(); trilha.save(update_fields=['status','concluido_em'])
        cert,_=CertificadoTreinamento.objects.get_or_create(loja=perfil.loja,colaborador=perfil,treinamento=trilha.treinamento,defaults={'codigo':uuid.uuid4().hex[:16].upper(),'carga_horaria_minutos':max(30,len(etapas)*15)})
        Notificacao.objects.create(loja=perfil.loja,usuario=request.user,titulo='Treinamento concluído',mensagem=f'{trilha.treinamento.titulo} concluído. Seu certificado virtual está disponível.',link=reverse('gestao_certificado',args=[cert.pk]))
    video_url=(atual.video_url if atual and atual.video_url else trilha.treinamento.video_url) if atual else ''
    video_embed=''
    if video_url:
        if 'youtu.be/' in video_url: video_embed='https://www.youtube.com/embed/'+video_url.split('youtu.be/',1)[1].split('?',1)[0]
        elif 'youtube.com/watch' in video_url and 'v=' in video_url: video_embed='https://www.youtube.com/embed/'+video_url.split('v=',1)[1].split('&',1)[0]
        elif 'youtube.com/embed/' in video_url: video_embed=video_url
    return render(request,'gestao/trilha_executar.html',{'loja':perfil.loja,'perfil':perfil,'trilha':trilha,'etapas':etapas,'atual':atual,'concluidas':concluidas,'total':len(etapas),'video_url':video_url,'video_embed':video_embed})

@plano_ativo
def workspace(request):
    loja=_empresa(request); instancia=None; editar=request.GET.get('editar','')
    if editar.isdigit(): instancia=NotaWorkspace.objects.filter(loja=loja,pk=int(editar)).first()
    form=NotaForm(request.POST or None,instance=instancia)
    if request.method=='POST' and form.is_valid():
        n=form.save(commit=False); n.loja=loja; n.autor=n.autor or request.user
        if n.status=='concluida' and not n.concluido_em: n.concluido_em=timezone.now()
        elif n.status!='concluida': n.concluido_em=None
        n.save(); return redirect('gestao_workspace')
    return render(request,'gestao/workspace.html',{'loja':loja,'form':form,'notas':NotaWorkspace.objects.filter(loja=loja).order_by('-fixada','-id'),'today':timezone.localdate()})

@plano_ativo
def ferramentas(request):
    loja=_empresa(request)
    if request.method=='POST':
        ferramenta=request.POST.get('ferramenta'); titulo=request.POST.get('titulo','').strip(); problema=request.POST.get('problema','').strip()
        campos={k:v for k,v in request.POST.items() if k not in ['csrfmiddlewaretoken','ferramenta','titulo','problema','processo','setor','inicio','fim','status'] and isinstance(v,str) and v.strip()}
        if ferramenta in dict(ProjetoQualidade.FERRAMENTAS) and titulo:
            status=request.POST.get('status','andamento')
            if status not in dict(ProjetoQualidade._meta.get_field('status').choices): status='andamento'
            processo=_fk_empresa(Processo,loja,request.POST.get('processo')); setor=_fk_empresa(Setor,loja,request.POST.get('setor'))
            projeto=ProjetoQualidade.objects.create(loja=loja,ferramenta=ferramenta,titulo=titulo,problema=problema,responsavel=request.user.get_full_name() or request.user.username,dados=campos,status=status,processo=processo,setor=setor,inicio=_data_post(request,'inicio'),fim=_data_post(request,'fim'),concluido_em=timezone.now() if status=='concluido' else None)
            _criar_etapas_metodologicas(projeto)
            RegistroAuditoriaSistema.objects.create(loja=loja,usuario=request.user,acao='analise_criada',objeto=f'{projeto.get_ferramenta_display()} #{projeto.id}',descricao=f'{projeto.titulo} • {projeto.processo or "Sem processo"} • {projeto.setor or "Sem setor"}')
            perfil=getattr(request.user,'perfil_colaborador',None)
            if perfil and status=='concluido':
                PontuacaoAtividade.objects.create(loja=loja,colaborador=perfil,categoria='qualidade',ferramenta=ferramenta,titulo=f'Aplicação concluída {projeto.get_ferramenta_display()} #{projeto.id}',pontos=25)
                perfil.pontos+=25; perfil.nivel=1+(perfil.pontos//500); perfil.save(update_fields=['pontos','nivel'])
            messages.success(request,f'{projeto.get_ferramenta_display()} salvo com sucesso. Ele já está visível no histórico e na Visão Geral.')
            return redirect('gestao_analise_detalhe',pk=projeto.pk)
    return render(request,'gestao/ferramentas.html',{'loja':loja,'projetos':ProjetoQualidade.objects.filter(loja=loja).select_related('processo','setor').order_by('-id')[:30],'processos_lista':Processo.objects.filter(loja=loja,status='ativo'),'setores_lista':Setor.objects.filter(loja=loja,ativo=True)})

@plano_ativo
def analise_detalhe(request,pk):
    loja=_empresa(request); projeto=get_object_or_404(ProjetoQualidade,loja=loja,pk=pk)
    _criar_etapas_metodologicas(projeto)
    return render(request,'gestao/analise_detalhe.html',{'loja':loja,'projeto':projeto,'etapas':projeto.etapas_cronograma.select_related('responsavel__usuario'),'colaboradores':Colaborador.objects.filter(loja=loja,ativo=True,status_cadastro='aprovado').select_related('usuario')})

@plano_ativo
def analise_salvar(request,pk):
    loja=_empresa(request); projeto=get_object_or_404(ProjetoQualidade,loja=loja,pk=pk)
    if request.method=='POST':
        anterior=projeto.status; novo=request.POST.get('status',projeto.status)
        if novo not in dict(ProjetoQualidade._meta.get_field('status').choices): novo=projeto.status
        projeto.inicio=_data_post(request,'inicio'); projeto.fim=_data_post(request,'fim'); projeto.status=novo
        if novo=='concluido' and anterior!='concluido': projeto.concluido_em=timezone.now()
        elif novo!='concluido': projeto.concluido_em=None
        projeto.save(update_fields=['inicio','fim','status','concluido_em','atualizado_em'])
        RegistroAuditoriaSistema.objects.create(loja=loja,usuario=request.user,acao='analise_atualizada',objeto=f'{projeto.get_ferramenta_display()} #{projeto.id}',descricao=f'Status: {projeto.get_status_display()}')
        perfil=getattr(request.user,'perfil_colaborador',None)
        if novo=='concluido' and anterior!='concluido' and perfil:
            chave=f'Aplicação concluída {projeto.get_ferramenta_display()} #{projeto.id}'
            if not PontuacaoAtividade.objects.filter(loja=loja,colaborador=perfil,titulo=chave).exists():
                PontuacaoAtividade.objects.create(loja=loja,colaborador=perfil,categoria='qualidade',ferramenta=projeto.ferramenta,titulo=chave,pontos=25)
                perfil.pontos+=25; perfil.nivel=1+(perfil.pontos//500); perfil.save(update_fields=['pontos','nivel'])
        messages.success(request,'Plano atualizado no mesmo registro.')
    return redirect('gestao_analise_detalhe',pk=pk)

@plano_ativo
def processo_rapido(request):
    if request.method!='POST': return JsonResponse({'ok':False,'erro':'Método inválido'},status=405)
    loja=_empresa(request); nome=request.POST.get('nome','').strip()
    if not nome: return JsonResponse({'ok':False,'erro':'Informe o nome do processo.'},status=400)
    setor=_fk_empresa(Setor,loja,request.POST.get('setor'))
    processo=Processo.objects.create(loja=loja,nome=nome,codigo=request.POST.get('codigo','').strip(),objetivo=request.POST.get('objetivo','').strip(),responsavel=request.POST.get('responsavel','').strip(),setor=setor)
    RegistroAuditoriaSistema.objects.create(loja=loja,usuario=request.user,acao='processo_criado',objeto=f'Processo #{processo.id}',descricao=processo.nome)
    return JsonResponse({'ok':True,'id':processo.id,'nome':processo.nome})

@plano_ativo
def colaboradores(request):
    loja=_empresa(request)
    if request.method=='POST':
        nome=request.POST.get('nome','').strip(); email=request.POST.get('email','').strip().lower(); setor=_fk_empresa(Setor,loja,request.POST.get('setor')); papel=request.POST.get('papel','colaborador')
        if papel not in dict(Colaborador._meta.get_field('papel').choices): papel='colaborador'
        if nome and email and not User.objects.filter(username=email).exists():
            u=User.objects.create(username=email,email=email,first_name=nome,is_active=False); u.set_unusable_password(); u.save()
            Colaborador.objects.create(loja=loja,usuario=u,setor=setor,cargo=request.POST.get('cargo',''),papel=papel)
            uid=urlsafe_base64_encode(force_bytes(u.pk)); token=default_token_generator.make_token(u); base=getattr(settings,'PLATFORM_BASE_URL','').rstrip('/'); link=base+reverse('gestao_ativar_colaborador',args=[uid,token])
            try: enviar_email(email,f'Convite para {loja.nome} na Nexa Gestão',f'<h2>{loja.nome} convidou você</h2><p>Ative seu acesso e crie sua própria senha.</p><p><a href="{link}">Ativar meu acesso</a></p>')
            except Exception as exc: print('CONVITE COLABORADOR:',exc)
            messages.success(request,'Convite criado. O colaborador define a própria senha pelo link enviado ao e-mail.')
        else: messages.error(request,'Preencha nome/e-mail ou use outro e-mail.')
        return redirect('gestao_colaboradores')
    return render(request,'gestao/colaboradores.html',{'loja':loja,'colaboradores':Colaborador.objects.filter(loja=loja).select_related('usuario','setor','supervisor__usuario'),'setores':Setor.objects.filter(loja=loja),'supervisores':Colaborador.objects.filter(loja=loja,ativo=True,status_cadastro='aprovado').select_related('usuario'),'papeis':Colaborador._meta.get_field('papel').choices})

def ativar_colaborador(request,uidb64,token):
    try: u=User.objects.get(pk=urlsafe_base64_decode(uidb64).decode())
    except Exception: u=None
    if not u or not default_token_generator.check_token(u,token): return render(request,'gestao/ativar_colaborador.html',{'invalido':True})
    if request.method=='POST':
        senha=request.POST.get('senha',''); confirmar=request.POST.get('confirmar','')
        if len(senha)<8 or senha!=confirmar: messages.error(request,'Use pelo menos 8 caracteres e confirme a mesma senha.')
        else:
            u.set_password(senha); u.is_active=True; u.save(update_fields=['password','is_active']); messages.success(request,'Acesso ativado. Agora você pode entrar.'); return redirect('login_loja')
    return render(request,'gestao/ativar_colaborador.html',{'usuario':u})

def _ciclo_jogo(perfil, jogo):
    """Pontuação de simulação: no máximo uma recompensa por semana ISO."""
    hoje=timezone.localdate(); inicio=hoje-timedelta(days=hoje.weekday()); fim=inicio+timedelta(days=6)
    chave=f'{jogo}:{inicio.isoformat()}'
    ja=PontuacaoAtividade.objects.filter(loja=perfil.loja,colaborador=perfil,categoria='jogo',ferramenta=chave).exists() if perfil else False
    return {'inicio':inicio,'fim':fim,'chave':chave,'pontuavel':not ja,'proxima':fim+timedelta(days=1)}

def _premiar_simulacao(loja, perfil, jogo, titulo, pontos, total, detalhes):
    if not perfil: return 0
    ciclo=_ciclo_jogo(perfil,jogo)
    TentativaJogo.objects.create(loja=loja,colaborador=perfil,jogo=jogo,pontuacao=pontos,total=total,detalhes={**detalhes,'ciclo':ciclo['inicio'].isoformat(),'pontuavel':ciclo['pontuavel']})
    if not ciclo['pontuavel']: return 0
    return conceder_pontos(perfil,'jogo',ciclo['chave'],titulo,pontos,{**detalhes,'ciclo':ciclo['inicio'].isoformat()},unico=True)

@plano_ativo
def academia(request):
    loja=_empresa(request); perfil=getattr(request.user,'perfil_colaborador',None)
    ciclos={j:_ciclo_jogo(perfil,j) for j in ('phishing','lean','causa_raiz')} if perfil else {}
    return render(request,'gestao/academia.html',{'loja':loja,'perfil':perfil,'tentativas':TentativaJogo.objects.filter(loja=loja,colaborador=perfil).order_by('-id')[:10] if perfil else [],'ciclos':ciclos})

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
            ganhos=_premiar_simulacao(loja,perfil,'phishing','Simulação Caixa de Entrada Segura',pontos,100,{'acertos':acertos,'total':len(questoes)}); resultado['ganhos']=ganhos; resultado['ciclo']=_ciclo_jogo(perfil,'phishing')
            if acertos==len(questoes): ConquistaColaborador.objects.get_or_create(loja=loja,colaborador=perfil,codigo='phishing_perfeito',defaults={'titulo':'Radar Antiphishing','descricao':'Acertou 100% em uma simulação de phishing.'})
    return render(request,'gestao/jogo_phishing.html',{'loja':loja,'questoes':questoes,'resultado':resultado})

@plano_ativo
def lgpd(request):
    loja=_empresa(request)
    treinamento_lgpd,_=Treinamento.objects.get_or_create(loja=loja,titulo='LGPD no dia a dia',defaults={'descricao':'Trilha didática sobre privacidade, dados pessoais e boas práticas no trabalho.','categoria':'LGPD','pontos':120,'obrigatorio':True,'nota_minima':70})
    if not treinamento_lgpd.etapas.exists():
        slides=[('O que é a LGPD?','Entenda por que a lei existe e como ela protege pessoas no uso de dados pessoais.'),('Dados pessoais e dados sensíveis','Aprenda a reconhecer informações que identificam pessoas e dados que exigem cuidado reforçado.'),('Cuidados no trabalho','Use somente os dados necessários, compartilhe apenas com quem precisa e proteja documentos e acessos.'),('Situações de risco','Phishing, envio ao destinatário errado, exposição de planilhas e acessos indevidos podem gerar incidentes.'),('Teste final','Revise os conceitos e registre sua conclusão da trilha.') ]
        for ordem,(titulo,descricao) in enumerate(slides,1): EtapaTreinamento.objects.create(loja=loja,treinamento=treinamento_lgpd,ordem=ordem,titulo=titulo,descricao=descricao,pontos=20,pergunta='Qual foi o principal aprendizado desta etapa?' if ordem==5 else '')
    form=LGPDForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        r=form.save(commit=False); r.loja=loja; r.usuario=request.user; ip=request.META.get('REMOTE_ADDR',''); r.ip_hash=hashlib.sha256(ip.encode()).hexdigest() if ip else ''; r.save(); messages.success(request,'Registro LGPD documentado.'); return redirect('gestao_lgpd')
    return render(request,'gestao/lgpd.html',{'loja':loja,'form':form,'treinamento_lgpd':treinamento_lgpd,'registros':RegistroLGPD.objects.filter(loja=loja).order_by('-registrado_em')[:30]})

@login_required
def portal_colaborador(request):
    perfil=getattr(request.user,'perfil_colaborador',None)
    if not perfil: return redirect('gestao_dashboard')
    loja=perfil.loja; sincronizar_nivel(perfil)
    ranking_ids=list(Colaborador.objects.filter(loja=loja,ativo=True,ranking_visivel=True).order_by('-pontos','criado_em').values_list('id',flat=True))
    posicao=(ranking_ids.index(perfil.id)+1) if perfil.id in ranking_ids else None
    return render(request,'gestao/portal_colaborador.html',{'loja':loja,'perfil':perfil,'nivel_info':progresso_nivel(perfil.pontos),'posicao_ranking':posicao,'tarefas':Tarefa.objects.filter(loja=loja,responsavel=perfil).exclude(status='concluida'),'trilhas':TrilhaColaborador.objects.filter(loja=loja,colaborador=perfil).select_related('treinamento'),'conquistas':ConquistaColaborador.objects.filter(loja=loja,colaborador=perfil).order_by('-concedida_em'),'notificacoes_novas':Notificacao.objects.filter(loja=loja,usuario=request.user,lida=False).count(),'certificados':CertificadoTreinamento.objects.filter(loja=loja,colaborador=perfil).select_related('treinamento').order_by('-emitido_em'),'historico_pontos':PontuacaoAtividade.objects.filter(loja=loja,colaborador=perfil).order_by('-criado_em')[:12],'meus_indicadores':Indicador.objects.filter(loja=loja,ativo=True,responsavel_colaborador=perfil).prefetch_related('medicoes')[:8]})


def meus_indicadores(request):
    perfil = getattr(request.user, 'perfil_colaborador', None)
    if not perfil:
        return redirect('gestao_dashboard')
    itens = Indicador.objects.filter(
        loja=perfil.loja,
        ativo=True,
        responsavel_colaborador=perfil
    ).select_related('processo').prefetch_related('medicoes')
    return render(request, 'gestao/meus_indicadores.html', {
        'loja': perfil.loja,
        'perfil': perfil,
        'itens': itens,
    })


def meus_treinamentos(request):
    perfil = getattr(request.user, 'perfil_colaborador', None)
    if not perfil:
        return redirect('gestao_dashboard')
    trilhas = TrilhaColaborador.objects.filter(
        loja=perfil.loja,
        colaborador=perfil
    ).select_related('treinamento').order_by('status', 'prazo')
    return render(request, 'gestao/meus_treinamentos.html', {
        'loja': perfil.loja,
        'perfil': perfil,
        'trilhas': trilhas,
    })


def minhas_notas(request):
    perfil = getattr(request.user, 'perfil_colaborador', None)
    if not perfil:
        return redirect('gestao_dashboard')
    instancia=None
    editar=request.GET.get('editar','')
    if editar.isdigit(): instancia=NotaWorkspace.objects.filter(loja=perfil.loja,autor=request.user,pk=int(editar)).first()
    form=NotaForm(request.POST or None,instance=instancia)
    if request.method == 'POST' and form.is_valid():
        n=form.save(commit=False); n.loja=perfil.loja; n.autor=request.user
        if n.status=='concluida' and not n.concluido_em: n.concluido_em=timezone.now()
        elif n.status!='concluida': n.concluido_em=None
        n.save(); messages.success(request, 'Nota salva.'); return redirect('gestao_minhas_notas')
    notas=NotaWorkspace.objects.filter(loja=perfil.loja,autor=request.user).order_by('-fixada','-atualizado_em')
    return render(request,'gestao/minhas_notas.html',{'loja':perfil.loja,'perfil':perfil,'form':form,'notas':notas,'today':timezone.localdate()})

def portal_empresa_publica(request,slug):
    from lojas.models import Loja
    loja=get_object_or_404(Loja,slug=slug)
    loja.verificar_licenca()
    if not loja.ativa:return render(request,'gestao/portal_indisponivel.html',{'loja':loja},status=403)
    return render(request,'gestao/portal_empresa.html',{'loja':loja})

def portal_empresa(request):
    loja=getattr(request,'loja',None)
    if not loja:return redirect('root_view')
    loja.verificar_licenca()
    if not loja.ativa:return render(request,'gestao/portal_indisponivel.html',{'loja':loja},status=403)
    return render(request,'gestao/portal_empresa.html',{'loja':loja})

@plano_ativo
def tarefa_status(request):
    if request.method!='POST': return redirect('gestao_tarefas')
    loja=_empresa(request); tarefa_id=request.POST.get('id','')
    if not tarefa_id.isdigit():
        messages.error(request,'Tarefa inválida.'); return redirect('gestao_tarefas')
    t=get_object_or_404(Tarefa,loja=loja,pk=int(tarefa_id))
    status=request.POST.get('status')
    if status in dict(Tarefa.STATUS):
        mudou=t.status!=status; t.status=status; t.save(update_fields=['status','atualizado_em'])
        if mudou and status=='concluida' and t.responsavel:
            chave=f'Tarefa concluída #{t.id}'
            if not PontuacaoAtividade.objects.filter(loja=loja,colaborador=t.responsavel,titulo=chave).exists():
                PontuacaoAtividade.objects.create(loja=loja,colaborador=t.responsavel,categoria='melhoria',ferramenta='tarefas',titulo=chave,pontos=20)
                t.responsavel.pontos+=20; t.responsavel.nivel=1+(t.responsavel.pontos//500); t.responsavel.save(update_fields=['pontos','nivel'])
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
    sincronizar_nivel(perfil); return render(request,'gestao/perfil.html',{'loja':perfil.loja,'perfil':perfil,'nivel_info':progresso_nivel(perfil.pontos),'form':form,'historico':historico,'conquistas':conquistas})

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
    base=Notificacao.objects.filter(loja=loja,usuario=request.user)
    if request.method=='GET':
        base.filter(lida=False).update(lida=True)
    if request.method=='POST' and request.POST.get('acao')=='marcar_lidas':
        base.filter(lida=False).update(lida=True); return redirect('gestao_notificacoes')
    if request.method=='POST' and request.POST.get('acao')=='enviar' and not perfil:
        titulo=request.POST.get('titulo','').strip(); mensagem=request.POST.get('mensagem','').strip(); destino=request.POST.get('destino','empresa'); alvo=request.POST.get('alvo','')
        pessoas=Colaborador.objects.filter(loja=loja,ativo=True,status_cadastro='aprovado').select_related('usuario')
        if destino=='setor' and alvo:
            setor=_fk_empresa(Setor,loja,alvo); pessoas=pessoas.filter(setor=setor) if setor else pessoas.none()
        elif destino=='colaborador' and alvo:
            colaborador=_fk_empresa(Colaborador,loja,alvo); pessoas=pessoas.filter(pk=colaborador.pk) if colaborador else pessoas.none()
        if titulo:
            for c in pessoas: Notificacao.objects.create(loja=loja,usuario=c.usuario,titulo=titulo,mensagem=mensagem,link=reverse('portal_colaborador'))
            messages.success(request,f'Notificação enviada para {pessoas.count()} pessoa(s).')
        return redirect('gestao_notificacoes')
    return render(request,'gestao/notificacoes.html',{'loja':loja,'itens':base[:50],'pode_enviar':not perfil,'setores':Setor.objects.filter(loja=loja,ativo=True),'colaboradores':Colaborador.objects.filter(loja=loja,ativo=True,status_cadastro='aprovado').select_related('usuario')})

@login_required
def notificacao_abrir(request,pk):
    perfil=getattr(request.user,'perfil_colaborador',None); loja=perfil.loja if perfil else _empresa(request)
    n=get_object_or_404(Notificacao,pk=pk,loja=loja,usuario=request.user)
    if not n.lida:
        n.lida=True; n.save(update_fields=['lida'])
    destino=n.link or ''
    if destino in ['/gestao/colaborador/','/painel/colaborador/']:
        destino=reverse('portal_colaborador')
    if destino and not destino.startswith('/'):
        destino=''
    return redirect(destino or ('portal_colaborador' if perfil else 'gestao_dashboard'))

@plano_ativo
def comentar_tarefa(request,pk):
    loja=_empresa(request); tarefa=get_object_or_404(Tarefa,pk=pk,loja=loja)
    if request.method=='POST' and request.POST.get('texto','').strip():
        ComentarioTarefa.objects.create(loja=loja,tarefa=tarefa,autor=request.user,texto=request.POST['texto'].strip())
        RegistroAuditoriaSistema.objects.create(loja=loja,usuario=request.user,acao='comentario',objeto=f'Tarefa #{tarefa.id}',descricao='Comentário adicionado à tarefa.')
        if tarefa.responsavel and tarefa.responsavel.usuario_id!=request.user.id:
            Notificacao.objects.create(loja=loja,usuario=tarefa.responsavel.usuario,titulo='Novo comentário em tarefa',mensagem=tarefa.titulo,link=reverse('gestao_tarefas'))
    return redirect('gestao_tarefas')

@plano_ativo
def auditoria_sistema(request):
    loja=_empresa(request)
    return render(request,'gestao/auditoria_sistema.html',{'loja':loja,'itens':RegistroAuditoriaSistema.objects.filter(loja=loja).select_related('usuario')[:100]})

@plano_ativo
def metas_equipe(request):
    return _crud(request,MetaEquipe,MetaEquipeForm,'Metas & Desafios de Equipe')

def _premiar_jogo(loja,perfil,jogo,titulo,pontos,total,detalhes):
    return _premiar_simulacao(loja,perfil,jogo,titulo,pontos,total,detalhes)

@plano_ativo
def jogo_lean(request):
    loja=_empresa(request); perfil=getattr(request.user,'perfil_colaborador',None)
    questoes=[('q1','Produzir antes da demanda real','superproducao'),('q2','Operador aguardando liberação da máquina','espera'),('q3','Levar material várias vezes entre prédios','transporte'),('q4','Refazer uma peça fora de especificação','defeitos'),('q5','Funcionário treinado sem autonomia para sugerir melhorias','talento')]
    opcoes=[('superproducao','Superprodução'),('espera','Espera'),('transporte','Transporte'),('defeitos','Defeitos'),('talento','Talento não aproveitado')]; resultado=None
    if request.method=='POST':
        acertos=sum(request.POST.get(q)==c for q,_,c in questoes); pontos=acertos*20; resultado={'acertos':acertos,'total':len(questoes),'pontos':pontos}; resultado['ganhos']=_premiar_jogo(loja,perfil,'lean','Caça ao desperdício',pontos,100,resultado); resultado['ciclo']=_ciclo_jogo(perfil,'lean') if perfil else None
        if perfil and acertos==len(questoes): ConquistaColaborador.objects.get_or_create(loja=loja,colaborador=perfil,codigo='lean_perfeito',defaults={'titulo':'Olhar Lean','descricao':'Identificou todos os desperdícios do desafio.'})
    return render(request,'gestao/jogo_lean.html',{'loja':loja,'questoes':questoes,'opcoes':opcoes,'resultado':resultado})

@plano_ativo
def jogo_causa_raiz(request):
    loja=_empresa(request); perfil=getattr(request.user,'perfil_colaborador',None); resultado=None
    etapas=[('q1','Máquina parou durante o turno. Qual primeira pergunta é mais útil?',['Quem é culpado?','Por que a máquina parou?','Quanto custa uma nova?'],1),('q2','Parou porque superaqueceu. Próximo passo?',['Por que superaqueceu?','Reiniciar e esquecer','Trocar o operador'],0),('q3','Superaqueceu por falta de lubrificação. O que investigar?',['Por que a lubrificação não ocorreu?','Comprar outra máquina','Encerrar análise'],0),('q4','A rotina não foi executada. Melhor conclusão?',['Registrar culpado','Investigar por que o processo permitiu a falha','Punir a equipe'],1)]
    if request.method=='POST':
        acertos=sum(str(c)==request.POST.get(q) for q,_,_,c in etapas); pontos=acertos*25; resultado={'acertos':acertos,'total':len(etapas),'pontos':pontos}; resultado['ganhos']=_premiar_jogo(loja,perfil,'causa_raiz','Detetive da causa raiz',pontos,100,resultado); resultado['ciclo']=_ciclo_jogo(perfil,'causa_raiz') if perfil else None
        if perfil and acertos==len(etapas): ConquistaColaborador.objects.get_or_create(loja=loja,colaborador=perfil,codigo='detetive_causa',defaults={'titulo':'Detetive da Causa Raiz','descricao':'Conduziu uma investigação sem atalhos ou culpabilização.'})
    return render(request,'gestao/jogo_causa_raiz.html',{'loja':loja,'etapas':etapas,'resultado':resultado})

def cadastro_colaborador_publico(request,slug):
    from lojas.models import Loja
    loja=get_object_or_404(Loja,slug=slug)
    loja.verificar_licenca()
    if not loja.ativa: return render(request,'gestao/portal_indisponivel.html',{'loja':loja},status=403)
    setores=Setor.objects.filter(loja=loja,ativo=True)
    supervisores=Colaborador.objects.filter(loja=loja,ativo=True,status_cadastro='aprovado').exclude(papel='colaborador').select_related('usuario')
    if request.method=='POST':
        nome=request.POST.get('nome','').strip(); email=request.POST.get('email','').strip().lower(); cpf=request.POST.get('cpf','').strip(); cargo=request.POST.get('cargo','').strip()
        if not request.POST.get('privacidade'):
            messages.error(request,'Confirme a ciência do aviso de privacidade para continuar.')
        elif not nome or not email:
            messages.error(request,'Informe nome e e-mail.')
        elif User.objects.filter(username=email).exists():
            messages.error(request,'Este e-mail já possui acesso ou solicitação cadastrada.')
        else:
            u=User.objects.create(username=email,email=email,first_name=nome,is_active=False); u.set_unusable_password(); u.save()
            setor=_fk_empresa(Setor,loja,request.POST.get('setor')); supervisor=_fk_empresa(Colaborador,loja,request.POST.get('supervisor'))
            Colaborador.objects.create(loja=loja,usuario=u,setor=setor,cargo=cargo,cpf=cpf,supervisor=supervisor,papel='colaborador',ativo=False,status_cadastro='pendente')
            Notificacao.objects.create(loja=loja,usuario=loja.dono,titulo='Novo colaborador aguardando aprovação',mensagem=f'{nome} solicitou acesso ao Portal da Empresa.',link=reverse('gestao_colaboradores'))
            messages.success(request,'Cadastro enviado. O gestor da empresa precisa aprovar seu acesso antes da ativação.')
            return redirect('cadastro_colaborador_publico',slug=slug)
    return render(request,'gestao/cadastro_colaborador_publico.html',{'loja':loja,'setores':setores,'supervisores':supervisores})

@plano_ativo
def aprovar_colaborador(request,pk):
    loja=_empresa(request); c=get_object_or_404(Colaborador,loja=loja,pk=pk)
    if request.method=='POST':
        setor=_fk_empresa(Setor,loja,request.POST.get('setor')); supervisor=_fk_empresa(Colaborador,loja,request.POST.get('supervisor'))
        c.status_cadastro='aprovado'; c.ativo=True; c.setor=setor or c.setor; c.cargo=request.POST.get('cargo',c.cargo); c.supervisor=supervisor or c.supervisor; c.save()
        u=c.usuario; uid=urlsafe_base64_encode(force_bytes(u.pk)); token=default_token_generator.make_token(u); base=getattr(settings,'PLATFORM_BASE_URL','').rstrip('/'); link=base+reverse('gestao_ativar_colaborador',args=[uid,token])
        try: enviar_email(u.email,f'Acesso aprovado em {loja.nome}',f'<h2>Seu cadastro foi aprovado</h2><p>Crie sua própria senha para acessar o portal.</p><p><a href="{link}">Ativar meu acesso</a></p>')
        except Exception as exc: print('APROVACAO COLABORADOR:',exc)
        messages.success(request,'Colaborador aprovado. O link para criação da senha foi enviado por e-mail.')
    return redirect('gestao_colaboradores')

@plano_ativo
def treinamentos_nexa(request):
    loja=_empresa(request)
    catalogo=[
      ('LGPD no dia a dia','Privacidade','Dados pessoais, boas práticas, incidentes e decisões seguras.',[
       ('Conceitos e princípios','A LGPD organiza como dados pessoais devem ser tratados durante todo o ciclo de vida. Dado pessoal é qualquer informação relacionada a uma pessoa identificada ou identificável. No trabalho, isso inclui nome, CPF, telefone, e-mail, matrícula, imagem e diversos registros digitais. O ponto central não é apenas guardar dados com segurança: é ter finalidade definida, usar somente o necessário, limitar acessos e manter transparência sobre o tratamento.\n\nNa prática, antes de coletar ou compartilhar uma informação, pergunte: para qual finalidade ela é necessária, quem realmente precisa acessá-la e por quanto tempo deve ser mantida?'),
       ('Dados pessoais e sensíveis','Dados pessoais sensíveis exigem cuidado reforçado porque podem gerar discriminação ou impactos relevantes. Exemplos incluem dados de saúde, biometria e informações sobre origem racial ou étnica. A classificação correta ajuda a empresa a definir controles proporcionais ao risco.\n\nEvite copiar bases inteiras quando apenas alguns campos são necessários. Compartilhamentos por planilhas, mensageiros e e-mail também fazem parte do tratamento e precisam seguir as mesmas regras de necessidade e acesso.'),
       ('Boas práticas no trabalho','Bloqueie a tela ao se afastar, confirme destinatários antes de enviar arquivos, não reutilize senhas e não deixe documentos pessoais expostos. Use somente canais autorizados pela empresa. Ao receber pedido de dados, confirme identidade, finalidade e autorização antes de responder.\n\nPrivacidade funciona melhor quando vira rotina operacional: menos cópias desnecessárias, acessos compatíveis com a função e descarte adequado reduzem risco sem depender apenas de tecnologia.'),
       ('Incidentes e resposta','Um incidente pode envolver envio ao destinatário errado, perda de equipamento, credencial comprometida, acesso indevido ou exposição de documentos. A prioridade é conter o evento, preservar evidências e comunicar rapidamente o canal responsável. Não apague rastros nem tente resolver silenciosamente.\n\nRegistre o que aconteceu, quando foi percebido, quais dados podem estar envolvidos e quais medidas imediatas foram tomadas. Essas informações permitem avaliar impacto e resposta.'),
       ('Avaliação final','Revise os princípios: finalidade, necessidade, acesso adequado, segurança e resposta a incidentes. Em cada cenário, identifique primeiro quais dados estão envolvidos, quem deveria acessá-los e qual é a ação mais segura. A avaliação final verifica aplicação prática, não memorização de termos.')]),
      ('Phishing e segurança digital','Segurança','Reconheça sinais de fraude, links suspeitos e engenharia social.',[
       ('Anatomia de uma mensagem','Uma mensagem legítima deve ser analisada pelo conjunto: remetente real, domínio, contexto, linguagem, links, anexos e ação solicitada. O nome exibido pode ser falsificado; por isso, observe o endereço completo. Ataques costumam imitar marcas, gestores ou fornecedores e explorar hábitos reais da empresa.\n\nAntes de clicar, compare o pedido com o processo normal. Uma cobrança inesperada, mudança de conta bancária ou solicitação de senha merece validação por outro canal.'),
       ('Sinais de phishing','Urgência artificial, ameaça de bloqueio, promessa incomum, erro de domínio, pedido de credencial e mudança repentina de procedimento são sinais importantes. Nenhum sinal isolado prova fraude, mas vários sinais combinados elevam o risco.\n\nEngenharia social tenta reduzir seu tempo de análise. Quando a mensagem força uma decisão imediata, interrompa o impulso e valide identidade, contexto e destino do link.'),
       ('Links e anexos','Passe o cursor sobre links para conferir o destino antes de abrir. Domínios parecidos podem trocar letras, usar subdomínios enganosos ou encurtadores. Anexos inesperados — especialmente executáveis, arquivos compactados ou documentos pedindo habilitação de conteúdo — exigem cautela.\n\nSe a tarefa puder ser feita entrando diretamente no site oficial, prefira abrir o endereço conhecido em vez de usar o link recebido.'),
       ('Como reagir','Não responda ao possível atacante, não encaminhe a mensagem para colegas como alerta informal e não teste o link. Use o mecanismo oficial de denúncia ou acione a equipe responsável. Se já clicou ou informou credenciais, comunique imediatamente; rapidez permite trocar senhas, encerrar sessões e reduzir impacto.\n\nRelatar um engano rapidamente é mais útil do que tentar escondê-lo.'),
       ('Avaliação por cenários','Agora aplique o método: contexto → remetente → domínio/link → solicitação → decisão. Em cada cenário, escolha entre confiar, validar por outro canal, reportar ou excluir. A meta é justificar a decisão pelos sinais observados, e não apenas marcar uma alternativa.')]),
      ('Caça aos desperdícios Lean','Melhoria contínua','Aprenda a identificar os oito desperdícios em situações operacionais.',[
       ('Visão Lean','Lean busca maximizar valor para o cliente reduzindo atividades que consomem recurso sem agregar valor. O primeiro passo é observar o fluxo real, não o procedimento imaginado. Tempo parado, deslocamentos, estoques e retrabalho escondem capacidade e aumentam lead time.'),
       ('Os oito desperdícios','Os oito desperdícios são defeitos, superprodução, espera, talento não utilizado, transporte, estoque, movimento e processamento excessivo. Eles podem aparecer juntos: produzir antes da necessidade gera estoque, que exige transporte e espaço e pode aumentar perdas.'),
       ('Exemplo industrial','Imagine um operador caminhando repetidamente para buscar etiquetas enquanto lotes aguardam liberação. Há movimento desnecessário e espera. Se o lote é produzido antes da demanda, também existe superprodução. Identificar o desperdício correto ajuda a atacar a causa e não apenas acelerar a pessoa.'),
       ('Priorização','Observe frequência, tempo perdido, impacto no cliente, segurança e custo. Priorize desperdícios relevantes e mensuráveis. Uma melhoria pequena e recorrente pode gerar mais resultado do que uma ocorrência rara e chamativa.'),
       ('Avaliação prática','Na simulação, procure evidências no cenário, classifique o desperdício e explique por que ele não agrega valor. Depois escolha uma contramedida que simplifique o fluxo em vez de apenas transferir o problema.')]),
      ('Detetive da causa raiz','Qualidade','Investigue problemas com fatos, 5 Porquês e Ishikawa.',[
       ('Problema x sintoma','Sintoma é o efeito percebido; causa é o mecanismo que contribui para produzi-lo. “Máquina parou” descreve o evento, mas não explica por que ocorreu. Uma boa definição informa o que aconteceu, onde, quando, frequência e impacto.'),
       ('Coleta de evidências','Antes de perguntar por quê, reúna registros, medições, horários, lotes, padrões e observação no local. Compare quando o problema ocorre e quando não ocorre. Evidência reduz a chance de transformar opinião em causa.'),
       ('5 Porquês','Cada resposta deve sustentar a pergunta seguinte. Não é obrigatório chegar exatamente ao quinto porquê. Pare quando alcançar uma causa verificável e tratável ou quando faltar evidência. Evite respostas baseadas em culpa, como “falta de atenção”, sem investigar condições do processo.'),
       ('Ishikawa 6M','Organize hipóteses em Método, Máquina, Mão de obra, Material, Meio ambiente e Medição. O diagrama amplia a investigação, mas não confirma causas. Depois do brainstorming, teste as hipóteses com fatos.'),
       ('Caso final','Construa uma linha lógica: problema bem definido → evidências → hipóteses → validação → causa provável → ação → verificação de eficácia. A solução deve atuar sobre a causa validada e ter indicador para confirmar o resultado.')]),
      ('5W2H aplicado','Qualidade','Transforme decisões em planos de ação claros e acompanháveis.',[
       ('Conceito','5W2H transforma uma intenção em plano verificável por sete perguntas. O objetivo não é preencher campos por obrigação, mas eliminar ambiguidades sobre entrega, motivo, local, prazo, responsabilidade, método e custo.'),
       ('Os 5W','What define a entrega concreta; Why registra a razão e o resultado esperado; Where delimita onde a ação ocorre; When estabelece a previsão; Who identifica quem responde pela execução. Evite verbos vagos como “melhorar” sem critério observável.'),
       ('Os 2H','How descreve como a ação será executada, incluindo método, recursos ou sequência. How much registra custo estimado ou informa que não há custo adicional. Esses campos ajudam a avaliar viabilidade antes da execução.'),
       ('Exemplo preenchido','Exemplo: revisar checklist de expedição para reduzir erro de separação; aplicar na Expedição; responsável Ana; início em 01/10 e previsão em 10/10; revisar itens com operadores, testar por três dias e aprovar nova versão; custo estimado zero. A conclusão real só é registrada quando o status muda para Concluído.'),
       ('Aplicação final','Depois de criar o plano, acompanhe as etapas, responsáveis, previsão, evidências e status. Alterações atualizam o mesmo plano. Um novo registro só deve existir quando houver um novo plano 5W2H.')]),
      ('PDCA aplicado','Qualidade','Planeje, execute, verifique e padronize melhorias.',[
       ('PLAN','Defina problema, situação atual, meta, causas e plano. Uma meta útil contém indicador e prazo. Planejar não é escolher uma solução rapidamente; é entender a lacuna e formular uma intervenção verificável.'),
       ('DO','Execute o plano em escala controlada quando possível. Registre quem fez, quando, evidências e desvios. Mudanças durante a execução precisam ficar visíveis para que o resultado possa ser interpretado corretamente.'),
       ('CHECK','Compare resultado com a linha de base e a meta usando dados equivalentes. Pergunte se a mudança realmente produziu o efeito e se surgiram consequências indesejadas. CHECK não é apenas marcar “feito”.'),
       ('ACT','Se a melhoria foi eficaz, incorpore-a ao padrão, treinamento e documentação. Se não foi, registre o aprendizado, ajuste hipóteses e inicie novo ciclo. ACT fecha o aprendizado e evita retorno ao estado anterior.'),
       ('Caso prático','Em um caso de retrabalho, acompanhe percentual antes e depois, volume produzido e período. Só padronize quando a comparação sustentar a melhoria. Se o resultado variar sem estabilidade, investigue antes de concluir.')]),
      ('Ishikawa 6M','Qualidade','Organize hipóteses de causa com método e evidências.',[
       ('Causa x correlação','Dois eventos ocorrerem juntos não prova causalidade. O Ishikawa organiza hipóteses para investigação. Cada causa relevante deve poder ser testada por observação, dado ou experimento.'),
       ('Os 6M','Método: padrões e sequência. Máquina: equipamentos e ferramentas. Mão de obra: capacitação, carga e ergonomia. Material: especificação e variação. Meio ambiente: temperatura, iluminação e organização. Medição: instrumento, método e qualidade do dado.'),
       ('Montagem do diagrama','Escreva o efeito de forma específica e reúna hipóteses por categoria. Aprofunde causas secundárias quando necessário. Evite preencher categorias apenas para completar o desenho.'),
       ('Validação','Priorize hipóteses plausíveis e procure evidências que possam confirmá-las ou refutá-las. Compare turnos, lotes, equipamentos ou condições. Uma hipótese não validada continua sendo hipótese.'),
       ('Caso prático','Para “etiqueta ilegível”, por exemplo, investigue impressora, configuração, material da etiqueta, limpeza, treinamento e método de inspeção. A ação final deve estar ligada à causa que os dados sustentarem.')]),
      ('FMEA de processo','Qualidade','Antecipe modos de falha e priorize riscos.',[
       ('Modo de falha','Modo de falha descreve como uma etapa pode deixar de cumprir sua função. Seja específico: “etiqueta com código incorreto” é mais útil do que “erro na etiqueta”. Um mesmo processo pode ter vários modos de falha.'),
       ('Severidade','Severidade estima o impacto do efeito caso a falha ocorra. Use uma escala definida pela empresa e critérios consistentes. Severidade alta merece atenção mesmo quando outros índices são baixos.'),
       ('Ocorrência','Ocorrência representa a probabilidade ou frequência da causa/falha. Baseie a nota em histórico, dados ou critério acordado, evitando escolher valores apenas por percepção.'),
       ('Detecção e RPN','Detecção avalia a capacidade dos controles atuais identificarem a falha antes do efeito. No modelo clássico, RPN = S × O × D. O número auxilia priorização, mas não substitui análise de severidade e contexto.'),
       ('Plano de redução','Defina ação, responsável e prazo para reduzir ocorrência, melhorar detecção ou, quando possível, reduzir severidade. Após implementar, reavalie S/O/D e registre evidências para demonstrar a mudança do risco.')]),
      ('Pareto 80/20','Qualidade','Priorize causas relevantes usando frequência e impacto.',[
       ('Princípio de Pareto','Pareto ordena categorias da maior para a menor contribuição para evidenciar concentração. A regra 80/20 é uma referência, não uma lei: os percentuais reais dependem dos dados.'),
       ('Preparação dos dados','Defina período, unidade e categorias mutuamente compreensíveis. Evite misturar causas, sintomas e tipos de ocorrência na mesma classificação. Dados inconsistentes geram prioridades enganosas.'),
       ('Gráfico','Ordene valores de forma decrescente e calcule participação acumulada. As barras mostram contribuição individual; a curva acumulada ajuda a visualizar quanto do total é explicado pelas primeiras categorias.'),
       ('Leitura','Comece pelas categorias de maior impacto quando houver capacidade de ação. Pareto mostra onde concentrar investigação, mas não prova por que o problema ocorre.'),
       ('Caso prático','Se três categorias representam 72% das reclamações, elas são candidatas à investigação prioritária. Depois das ações, repita o Pareto em período comparável para verificar se o perfil mudou.')]),
      ('5S na prática','Qualidade','Organização, limpeza, padronização e disciplina no ambiente.',[
       ('Seiri','Utilização: separar o necessário do desnecessário. Defina critérios para retirar excessos sem descartar itens importantes. O resultado esperado é liberar espaço e reduzir procura e confusão.'),
       ('Seiton','Ordenação: definir local, identificação e quantidade adequada para cada item. O objetivo é tornar fácil encontrar, usar e devolver, reduzindo movimento e tempo perdido.'),
       ('Seiso','Limpeza e inspeção: limpar enquanto se observa a origem de sujeira, vazamento, desgaste e anomalias. Não é apenas estética; é uma forma de inspeção do processo.'),
       ('Seiketsu','Padronização: transformar os três primeiros sensos em rotinas visuais, critérios, frequência e responsabilidades. Um padrão simples e visível facilita perceber desvios.'),
       ('Shitsuke','Disciplina: sustentar o padrão por comportamento, auditoria e melhoria. O objetivo não é punir, mas tornar o novo modo de trabalho parte da rotina e corrigir causas de reincidência.')]),
    ]
    itens=[]
    for titulo,categoria,descricao,etapas in catalogo:
        t,_=Treinamento.objects.get_or_create(loja=loja,titulo=titulo,defaults={'descricao':descricao,'categoria':categoria,'origem':'nexa','pontos':150,'nota_minima':70,'ativo':True})
        alter=[]
        if t.origem!='nexa': t.origem='nexa'; alter.append('origem')
        if t.pontos!=150: t.pontos=150; alter.append('pontos')
        if t.descricao!=descricao: t.descricao=descricao; alter.append('descricao')
        if alter: t.save(update_fields=alter)
        existentes={e.ordem:e for e in t.etapas.all()}
        for i,(nome,conteudo) in enumerate(etapas,1):
            e=existentes.get(i)
            pergunta='Explique com suas palavras como você aplicaria este conteúdo em uma situação real.' if i==len(etapas) else ''
            if e:
                e.titulo=nome; e.descricao=conteudo; e.pontos=30; e.pergunta=pergunta; e.save(update_fields=['titulo','descricao','pontos','pergunta'])
            else: EtapaTreinamento.objects.create(loja=loja,treinamento=t,ordem=i,titulo=nome,descricao=conteudo,pontos=30,pergunta=pergunta)
        itens.append(t)
    iniciar_id=request.GET.get('iniciar',''); perfil=getattr(request.user,'perfil_colaborador',None)
    if iniciar_id.isdigit() and perfil:
        treinamento=next((x for x in itens if x.pk==int(iniciar_id)),None)
        if treinamento:
            trilha,_=TrilhaColaborador.objects.get_or_create(loja=loja,colaborador=perfil,treinamento=treinamento)
            return redirect('gestao_trilha_executar',pk=trilha.pk)
    selecionado=None; curso_id=request.GET.get('curso','')
    if curso_id.isdigit(): selecionado=next((x for x in itens if x.pk==int(curso_id)),None)
    if perfil:
        status_trilhas={x.treinamento_id:x.status for x in TrilhaColaborador.objects.filter(loja=loja,colaborador=perfil,treinamento__in=itens)}
        for t in itens: t.status_colaborador=status_trilhas.get(t.id,'nao_iniciado')
    return render(request,'gestao/treinamentos_nexa.html',{'loja':loja,'itens':itens,'selecionado':selecionado})

@login_required
def certificado(request,pk):
    perfil=getattr(request.user,'perfil_colaborador',None)
    cert=get_object_or_404(CertificadoTreinamento,pk=pk)
    if perfil and cert.colaborador_id!=perfil.id: return redirect('portal_colaborador')
    if not perfil and cert.loja!=_empresa(request): return redirect('gestao_dashboard')
    return render(request,'gestao/certificado.html',{'loja':cert.loja,'cert':cert})

ETAPAS_METODOLOGICAS={
 'pdca':[('PLAN • Planejar','Definir problema, objetivo, causas, metas e plano.'),('DO • Executar','Executar o plano e registrar evidências.'),('CHECK • Verificar','Comparar resultado, meta e indicadores.'),('ACT • Agir/Padronizar','Padronizar o que funcionou ou corrigir e reiniciar o ciclo.')],
 '5w2h':[('Definir ação • What/Why','Definir o que será feito e por quê.'),('Planejar • Where/When/Who','Definir local, prazo e responsáveis.'),('Método e custo • How/How much','Detalhar como será executado e o custo previsto.'),('Executar ação','Realizar o planejado e anexar evidências.'),('Verificar e encerrar','Confirmar resultado, registrar conclusão e lições aprendidas.')],
 'ishikawa':[('Definir efeito/problema','Descrever claramente o efeito a investigar.'),('Levantar causas 6M','Mapear hipóteses em Método, Máquina, Mão de obra, Material, Meio ambiente e Medição.'),('Validar causas','Checar evidências e separar hipótese de causa confirmada.'),('Definir causa prioritária','Registrar causa(s) que exigem tratamento.'),('Planejar ação','Converter causas validadas em ações acompanháveis.')],
 '5porques':[('Definir problema','Descrever o fato observado com evidência.'),('Encadear os porquês','Investigar sucessivamente sem saltar para solução.'),('Validar causa raiz','Confirmar a causa provável com fatos.'),('Definir ação corretiva','Criar ação ligada à causa validada.'),('Verificar eficácia','Confirmar se o problema deixou de ocorrer.')],
 'pareto':[('Definir período e categorias','Estabelecer base comparável para análise.'),('Coletar e validar dados','Conferir frequência ou impacto das ocorrências.'),('Ordenar e analisar','Priorizar categorias de maior contribuição.'),('Definir prioridades','Selecionar os poucos vitais a tratar.'),('Acompanhar resultado','Repetir a medição após as ações.')],
 'sipoc':[('Definir escopo','Delimitar início e fim do processo.'),('Mapear Suppliers e Inputs','Registrar fornecedores e entradas.'),('Mapear Process','Descrever de 5 a 7 macroetapas.'),('Mapear Outputs e Customers','Registrar saídas e clientes.'),('Validar com envolvidos','Revisar interfaces, requisitos e responsáveis.')],
 'masp':[('1 • Identificação','Definir e dimensionar o problema.'),('2 • Observação','Estratificar e observar características.'),('3 • Análise','Investigar e validar causas.'),('4 • Plano de ação','Planejar contramedidas.'),('5 • Ação','Executar o plano.'),('6 • Verificação','Confirmar resultados e eficácia.'),('7 • Padronização','Incorporar o novo padrão.'),('8 • Conclusão','Registrar aprendizado e próximos passos.')],
 '5s':[('Seiri • Utilização','Separar necessário do desnecessário.'),('Seiton • Ordenação','Definir locais e identificação.'),('Seiso • Limpeza/inspeção','Eliminar sujeira e identificar anomalias.'),('Seiketsu • Padronização','Criar padrões visuais e rotinas.'),('Shitsuke • Disciplina','Sustentar, auditar e melhorar o padrão.')]
}

def _criar_etapas_metodologicas(projeto):
    if projeto.etapas_cronograma.exists(): return
    for ordem,(titulo,descricao) in enumerate(ETAPAS_METODOLOGICAS.get(projeto.ferramenta,[]),1):
        EtapaProjetoQualidade.objects.create(loja=projeto.loja,projeto=projeto,ordem=ordem,titulo=titulo,descricao=descricao)

def _notificar_etapa(etapa, anterior_id=None):
    c=etapa.responsavel
    if not c or c.pk==anterior_id: return
    link=reverse('gestao_analise_detalhe',args=[etapa.projeto_id])
    titulo=f'Nova etapa atribuída • {etapa.projeto.get_ferramenta_display()}'
    prazo = etapa.previsao.strftime("%d/%m/%Y") if hasattr(etapa.previsao, "strftime") else str(etapa.previsao or '')
    msg=f'{etapa.titulo} — {etapa.projeto.titulo}' + (f' • prazo {prazo}' if prazo else '')
    Notificacao.objects.create(loja=etapa.loja,usuario=c.usuario,titulo=titulo,mensagem=msg,link=link)
    if c.email_notificacoes and c.usuario.email:
        try: enviar_email(c.usuario.email,f'Nexa Gestão • {titulo}',f'<h2>{titulo}</h2><p>{msg}</p><p>Acesse a Nexa Gestão para acompanhar a etapa.</p>')
        except Exception as exc: print('EMAIL ETAPA QUALIDADE:',exc)

@plano_ativo
def etapa_qualidade_nova(request,pk):
    loja=_empresa(request); projeto=get_object_or_404(ProjetoQualidade,loja=loja,pk=pk)
    if request.method=='POST':
        ultima=projeto.etapas_cronograma.order_by('-ordem').first()
        responsavel=_fk_empresa(Colaborador,loja,request.POST.get('responsavel'))
        e=EtapaProjetoQualidade.objects.create(loja=loja,projeto=projeto,ordem=(ultima.ordem+1 if ultima else 1),titulo=request.POST.get('titulo','Nova etapa').strip() or 'Nova etapa',descricao=request.POST.get('descricao','').strip(),responsavel=responsavel,inicio=_data_post(request,'inicio'),previsao=_data_post(request,'previsao'),observacoes=request.POST.get('observacoes','').strip())
        _notificar_etapa(e)
        messages.success(request,'Etapa adicionada ao cronograma.')
    return redirect('gestao_analise_detalhe',pk=pk)

@plano_ativo
def etapa_qualidade_salvar(request,pk):
    loja=_empresa(request); e=get_object_or_404(EtapaProjetoQualidade,loja=loja,pk=pk)
    if request.method=='POST':
        anterior=e.responsavel_id; status_anterior=e.status
        responsavel=_fk_empresa(Colaborador,loja,request.POST.get('responsavel')); novo_status=request.POST.get('status',e.status)
        if novo_status not in dict(EtapaProjetoQualidade.STATUS): novo_status=e.status
        e.titulo=request.POST.get('titulo',e.titulo).strip() or e.titulo; e.descricao=request.POST.get('descricao','').strip(); e.responsavel=responsavel; e.inicio=_data_post(request,'inicio'); e.previsao=_data_post(request,'previsao'); e.status=novo_status; e.observacoes=request.POST.get('observacoes','').strip()
        if request.FILES.get('evidencia'): e.evidencia=request.FILES['evidencia']
        if e.status=='concluida' and status_anterior!='concluida': e.concluido_em=timezone.now()
        elif e.status!='concluida': e.concluido_em=None
        e.save(); _notificar_etapa(e,anterior)
        if e.status=='concluida' and status_anterior!='concluida' and e.responsavel:
            chave=f'Etapa qualidade #{e.pk}'
            if not PontuacaoAtividade.objects.filter(loja=loja,colaborador=e.responsavel,titulo=chave).exists():
                PontuacaoAtividade.objects.create(loja=loja,colaborador=e.responsavel,categoria='qualidade',ferramenta=e.projeto.ferramenta,titulo=chave,pontos=e.pontos,detalhes={'projeto':e.projeto.titulo,'etapa':e.titulo})
                e.responsavel.pontos+=e.pontos; e.responsavel.nivel=1+(e.responsavel.pontos//500); e.responsavel.save(update_fields=['pontos','nivel'])
                Notificacao.objects.create(loja=loja,usuario=e.responsavel.usuario,titulo=f'Parabéns! +{e.pontos} ⭐ pontos',mensagem=f'Você ganhou {e.pontos} pontos por concluir “{e.titulo}”.',link=reverse('portal_colaborador'))
        RegistroAuditoriaSistema.objects.create(loja=loja,usuario=request.user,acao='etapa_qualidade_atualizada',objeto=f'Etapa #{e.pk}',descricao=f'{e.projeto} • {e.titulo} • {e.get_status_display()}')
        messages.success(request,'Etapa atualizada.')
    return redirect('gestao_analise_detalhe',pk=e.projeto_id)


NEXA_AVALIACOES={
'LGPD no dia a dia':[('Qual atitude é mais adequada ao lidar com dados pessoais?',['Coletar tudo por precaução','Usar apenas o necessário para a finalidade','Compartilhar livremente dentro da empresa'],1),('Um envio de planilha com dados ao destinatário errado deve ser tratado como:',['Possível incidente a ser reportado','Situação sem importância','Apenas erro de digitação'],0),('Senha de acesso deve ser:',['Compartilhada com a equipe','Única e protegida','Anotada em local público'],1)],
'Phishing e segurança digital':[('Uma mensagem urgente pedindo senha é:',['Sinal de alerta','Rotina normal','Garantia de autenticidade'],0),('Mudança de conta bancária de fornecedor deve ser:',['Validada por outro canal','Aceita pelo link recebido','Ignorada para sempre'],0),('Link encurtado inesperado exige:',['Cautela e validação','Clique imediato','Encaminhamento geral'],0)],
'Caça aos desperdícios Lean':[('Produzir antes da demanda é:',['Superprodução','Espera','Defeito'],0),('Movimentação desnecessária de pessoas é:',['Movimentação','Estoque','Processamento'],0),('Retrabalho está ligado a:',['Defeitos','Transporte','Espera'],0)],
'Detetive da causa raiz':[('A análise de causa deve começar por:',['Fatos e problema bem definido','Culpado provável','Solução favorita'],0),('5 Porquês serve para:',['Aprofundar relações de causa','Calcular OEE','Organizar estoque'],0),('Ishikawa ajuda a:',['Estruturar hipóteses de causa','Emitir nota fiscal','Medir férias'],0)],
'5W2H aplicado':[('Who define:',['Responsável','Prazo','Custo'],0),('When define:',['Prazo','Método','Motivo'],0),('How much trata de:',['Custo/recursos','Local','Responsável'],0)],
'PDCA aplicado':[('PLAN corresponde a:',['Planejar','Executar','Padronizar'],0),('CHECK corresponde a:',['Verificar resultados','Executar ação','Definir cargo'],0),('ACT busca:',['Agir sobre resultados e padronizar','Ignorar desvios','Somente coletar dados'],0)],
'Ishikawa 6M':[('O diagrama organiza:',['Hipóteses de causa','Folha de pagamento','Contratos'],0),('Máquina é uma categoria dos:',['6M','5W','4P'],0),('Uma hipótese deve depois ser:',['Validada com evidências','Assumida como causa','Apagada'],0)],
'FMEA de processo':[('FMEA busca principalmente:',['Antecipar modos de falha e riscos','Registrar ponto','Criar organograma'],0),('Severidade avalia:',['Impacto do efeito','Frequência apenas','Facilidade de detectar apenas'],0),('Após priorizar risco, deve-se:',['Planejar e acompanhar ações','Encerrar sem ação','Excluir o registro'],0)],
'Pareto 80/20':[('Pareto ajuda a:',['Priorizar causas relevantes','Criar senha','Medir temperatura'],0),('Antes do gráfico é importante:',['Validar e categorizar dados','Escolher a causa preferida','Excluir ocorrências altas'],0),('Após ações, recomenda-se:',['Medir novamente','Nunca revisar','Trocar categorias sem dados'],0)],
'5S na prática':[('Seiri trata de:',['Utilização','Ordenação','Disciplina'],0),('Seiton trata de:',['Ordenação','Limpeza','Utilização'],0),('Shitsuke reforça:',['Disciplina e sustentação','Descarte apenas','Compra de equipamentos'],0)],
}

@login_required
def treinamento_nexa_avaliacao(request,pk):
    perfil=getattr(request.user,'perfil_colaborador',None)
    if not perfil: return redirect('gestao_dashboard')
    trilha=get_object_or_404(TrilhaColaborador,pk=pk,colaborador=perfil,loja=perfil.loja,treinamento__origem='nexa')
    questoes=NEXA_AVALIACOES.get(trilha.treinamento.titulo,[]); resultado=None
    if request.method=='POST' and questoes:
        acertos=sum(1 for i,q in enumerate(questoes) if request.POST.get(f'q{i}')==str(q[2]))
        nota=round(acertos/len(questoes)*100,2); pontos=round(trilha.treinamento.pontos*acertos/len(questoes))
        trilha.nota=nota; trilha.status='concluido'; trilha.concluido_em=timezone.now(); trilha.save(update_fields=['nota','status','concluido_em'])
        ganhos=conceder_pontos(perfil,'treinamento','treinamento_nexa',f'Nexa • {trilha.treinamento.titulo}',pontos,{'acertos':acertos,'total':len(questoes),'nota':nota},unico=True)
        if nota>=trilha.treinamento.nota_minima:
            CertificadoTreinamento.objects.get_or_create(loja=perfil.loja,colaborador=perfil,treinamento=trilha.treinamento,defaults={'codigo':uuid.uuid4().hex[:16].upper(),'carga_horaria_minutos':max(30,trilha.treinamento.etapas.count()*15)})
        if ganhos: Notificacao.objects.create(loja=perfil.loja,usuario=request.user,titulo=f'Treinamento Nexa concluído • +{ganhos} ⭐',mensagem=f'{trilha.treinamento.titulo}: {acertos}/{len(questoes)} acertos, nota {nota:.0f}%.',link=reverse('portal_colaborador'))
        resultado={'acertos':acertos,'total':len(questoes),'nota':nota,'pontos':ganhos,'aprovado':nota>=trilha.treinamento.nota_minima}
    return render(request,'gestao/treinamento_nexa_avaliacao.html',{'loja':perfil.loja,'perfil':perfil,'trilha':trilha,'questoes':questoes,'resultado':resultado})
