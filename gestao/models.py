from django.db import models
from django.conf import settings
from lojas.models import Loja

class BaseEmpresa(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    class Meta: abstract = True

class Processo(BaseEmpresa):
    STATUS=[('ativo','Ativo'),('revisao','Em revisão'),('inativo','Inativo')]
    nome=models.CharField(max_length=160); codigo=models.CharField(max_length=40, blank=True)
    objetivo=models.TextField(blank=True); responsavel=models.CharField(max_length=120, blank=True)
    entradas=models.TextField(blank=True); saidas=models.TextField(blank=True); riscos=models.TextField(blank=True)
    status=models.CharField(max_length=20, choices=STATUS, default='ativo')
    setor=models.ForeignKey('Setor',on_delete=models.SET_NULL,null=True,blank=True,related_name='processos')
    class Meta: ordering=['nome']; unique_together=[('loja','codigo')]
    def __str__(self): return self.nome

class Indicador(BaseEmpresa):
    PERIOD=[('mensal','Mensal'),('semanal','Semanal'),('diario','Diário')]
    nome=models.CharField(max_length=160); processo=models.ForeignKey(Processo,on_delete=models.SET_NULL,null=True,blank=True)
    unidade=models.CharField(max_length=30, default='%'); meta=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    sentido=models.CharField(max_length=10,choices=[('maior','Maior'),('menor','Menor')],default='maior')
    periodicidade=models.CharField(max_length=20,choices=PERIOD,default='mensal'); responsavel=models.CharField(max_length=120,blank=True)
    ativo=models.BooleanField(default=True)
    def __str__(self): return self.nome

class MedicaoIndicador(BaseEmpresa):
    indicador=models.ForeignKey(Indicador,on_delete=models.CASCADE,related_name='medicoes'); periodo=models.DateField()
    valor=models.DecimalField(max_digits=12,decimal_places=2); observacao=models.CharField(max_length=255,blank=True)
    class Meta: ordering=['-periodo']; unique_together=[('indicador','periodo')]

class PlanoAcao(BaseEmpresa):
    STATUS=[('aberto','Aberto'),('andamento','Em andamento'),('concluido','Concluído'),('atrasado','Atrasado')]
    titulo=models.CharField(max_length=180); origem=models.CharField(max_length=120,blank=True)
    o_que=models.TextField('O que'); por_que=models.TextField('Por quê',blank=True); onde=models.CharField(max_length=150,blank=True)
    quem=models.CharField(max_length=120,blank=True); quando=models.DateField(null=True,blank=True); como=models.TextField(blank=True)
    quanto=models.DecimalField(max_digits=12,decimal_places=2,null=True,blank=True); status=models.CharField(max_length=20,choices=STATUS,default='aberto')
    prioridade=models.CharField(max_length=10,choices=[('baixa','Baixa'),('media','Média'),('alta','Alta'),('critica','Crítica')],default='media')
    def __str__(self): return self.titulo

class NaoConformidade(BaseEmpresa):
    STATUS=[('aberta','Aberta'),('analise','Em análise'),('acao','Ação em curso'),('encerrada','Encerrada')]
    codigo=models.CharField(max_length=40,blank=True); titulo=models.CharField(max_length=180); descricao=models.TextField()
    processo=models.ForeignKey(Processo,on_delete=models.SET_NULL,null=True,blank=True); causa_raiz=models.TextField(blank=True)
    correcao=models.TextField(blank=True); responsavel=models.CharField(max_length=120,blank=True); prazo=models.DateField(null=True,blank=True)
    status=models.CharField(max_length=20,choices=STATUS,default='aberta'); severidade=models.IntegerField(default=3)
    def __str__(self): return self.titulo

class DocumentoGestao(BaseEmpresa):
    TIPO=[('politica','Política'),('procedimento','Procedimento'),('instrucao','Instrução de trabalho'),('registro','Registro'),('manual','Manual')]
    codigo=models.CharField(max_length=40,blank=True); titulo=models.CharField(max_length=180); tipo=models.CharField(max_length=20,choices=TIPO,default='procedimento')
    versao=models.CharField(max_length=20,default='1.0'); responsavel=models.CharField(max_length=120,blank=True); arquivo=models.FileField(upload_to='gestao/documentos/',blank=True,null=True)
    conteudo=models.TextField(blank=True); aprovado=models.BooleanField(default=False); proxima_revisao=models.DateField(null=True,blank=True)
    def __str__(self): return self.titulo

class Auditoria(BaseEmpresa):
    STATUS=[('planejada','Planejada'),('andamento','Em andamento'),('concluida','Concluída')]
    titulo=models.CharField(max_length=180); escopo=models.TextField(blank=True); auditor=models.CharField(max_length=120,blank=True)
    data=models.DateField(); status=models.CharField(max_length=20,choices=STATUS,default='planejada'); resultado=models.TextField(blank=True)
    def __str__(self): return self.titulo

class RequisitoISO(BaseEmpresa):
    norma=models.CharField(max_length=40,default='ISO 9001:2015'); clausula=models.CharField(max_length=20); titulo=models.CharField(max_length=180)
    status=models.CharField(max_length=20,choices=[('nao_iniciado','Não iniciado'),('andamento','Em andamento'),('conforme','Conforme'),('na','Não aplicável')],default='nao_iniciado')
    evidencia=models.TextField(blank=True); responsavel=models.CharField(max_length=120,blank=True)
    class Meta: ordering=['clausula']

class RiscoFMEA(BaseEmpresa):
    processo=models.ForeignKey(Processo,on_delete=models.CASCADE,related_name='fmeas'); modo_falha=models.CharField(max_length=180)
    efeito=models.TextField(blank=True); causa=models.TextField(blank=True); severidade=models.PositiveSmallIntegerField(default=1)
    ocorrencia=models.PositiveSmallIntegerField(default=1); deteccao=models.PositiveSmallIntegerField(default=1); acao=models.TextField(blank=True)
    @property
    def rpn(self): return self.severidade*self.ocorrencia*self.deteccao

class RegistroProducao(BaseEmpresa):
    data=models.DateField(); linha=models.CharField(max_length=120); tempo_planejado=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    tempo_operando=models.DecimalField(max_digits=10,decimal_places=2,default=0); quantidade_total=models.PositiveIntegerField(default=0); quantidade_boa=models.PositiveIntegerField(default=0)
    ciclo_ideal=models.DecimalField(max_digits=10,decimal_places=4,default=0)
    @property
    def disponibilidade(self): return float(self.tempo_operando/self.tempo_planejado) if self.tempo_planejado else 0
    @property
    def qualidade(self): return self.quantidade_boa/self.quantidade_total if self.quantidade_total else 0
    @property
    def performance(self): return min((float(self.ciclo_ideal)*self.quantidade_total/float(self.tempo_operando)),1) if self.tempo_operando else 0
    @property
    def oee(self): return self.disponibilidade*self.performance*self.qualidade

class IdeiaMelhoria(BaseEmpresa):
    titulo=models.CharField(max_length=180); descricao=models.TextField(); autor=models.CharField(max_length=120,blank=True)
    status=models.CharField(max_length=20,choices=[('nova','Nova'),('avaliacao','Em avaliação'),('aprovada','Aprovada'),('implantada','Implantada')],default='nova')
    votos=models.PositiveIntegerField(default=0)

class Setor(BaseEmpresa):
    nome=models.CharField(max_length=120); descricao=models.TextField(blank=True); gestor=models.CharField(max_length=120,blank=True); ativo=models.BooleanField(default=True)
    class Meta: ordering=['nome']; unique_together=[('loja','nome')]
    def __str__(self): return self.nome

class Colaborador(models.Model):
    loja=models.ForeignKey(Loja,on_delete=models.CASCADE,related_name='colaboradores_gestao'); usuario=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='perfil_colaborador')
    setor=models.ForeignKey(Setor,on_delete=models.SET_NULL,null=True,blank=True); cargo=models.CharField(max_length=120,blank=True); matricula=models.CharField(max_length=60,blank=True)
    pontos=models.PositiveIntegerField(default=0); nivel=models.PositiveIntegerField(default=1); ativo=models.BooleanField(default=True); criado_em=models.DateTimeField(auto_now_add=True)
    papel=models.CharField(max_length=20,choices=[('colaborador','Colaborador'),('gestor_setor','Gestor de setor'),('gestor_empresa','Gestor da empresa')],default='colaborador'); email_notificacoes=models.BooleanField(default=True)
    foto=models.ImageField(upload_to='gestao/perfis/',blank=True,null=True); bio=models.CharField(max_length=500,blank=True); titulo_perfil=models.CharField(max_length=120,blank=True)
    perfil_visivel=models.BooleanField(default=True); ranking_visivel=models.BooleanField(default=True); mostrar_conquistas=models.BooleanField(default=True)
    def __str__(self): return self.usuario.get_full_name() or self.usuario.username

class Tarefa(BaseEmpresa):
    STATUS=[('backlog','Backlog'),('fazer','A fazer'),('andamento','Em andamento'),('revisao','Em revisão'),('concluida','Concluída')]
    titulo=models.CharField(max_length=180); descricao=models.TextField(blank=True); setor=models.ForeignKey(Setor,on_delete=models.SET_NULL,null=True,blank=True)
    responsavel=models.ForeignKey(Colaborador,on_delete=models.SET_NULL,null=True,blank=True); inicio=models.DateField(null=True,blank=True); fim=models.DateField(null=True,blank=True)
    status=models.CharField(max_length=20,choices=STATUS,default='fazer'); prioridade=models.CharField(max_length=10,choices=[('baixa','Baixa'),('media','Média'),('alta','Alta'),('critica','Crítica')],default='media')
    def __str__(self): return self.titulo

class NotaWorkspace(BaseEmpresa):
    titulo=models.CharField(max_length=120,blank=True); conteudo=models.TextField(); setor=models.ForeignKey(Setor,on_delete=models.SET_NULL,null=True,blank=True)
    cor=models.CharField(max_length=20,default='amarelo'); autor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)
    fixada=models.BooleanField(default=False)

class ProjetoQualidade(BaseEmpresa):
    FERRAMENTAS=[('pdca','PDCA'),('5w2h','5W2H'),('ishikawa','Ishikawa'),('5porques','5 Porquês'),('pareto','Pareto'),('sipoc','SIPOC'),('masp','MASP'),('5s','5S')]
    ferramenta=models.CharField(max_length=20,choices=FERRAMENTAS); titulo=models.CharField(max_length=180); problema=models.TextField(blank=True); responsavel=models.CharField(max_length=120,blank=True)
    processo=models.ForeignKey(Processo,on_delete=models.SET_NULL,null=True,blank=True,related_name='analises_qualidade'); setor=models.ForeignKey('Setor',on_delete=models.SET_NULL,null=True,blank=True,related_name='analises_qualidade')
    inicio=models.DateField(null=True,blank=True); fim=models.DateField(null=True,blank=True); concluido_em=models.DateTimeField(null=True,blank=True); status=models.CharField(max_length=20,choices=[('rascunho','Rascunho'),('andamento','Em andamento'),('concluido','Concluído')],default='rascunho')
    dados=models.JSONField(default=dict,blank=True)
    def __str__(self): return f'{self.get_ferramenta_display()} • {self.titulo}'

class Treinamento(BaseEmpresa):
    titulo=models.CharField(max_length=180); descricao=models.TextField(blank=True); categoria=models.CharField(max_length=80,default='Qualidade'); conteudo=models.TextField(blank=True)
    pontos=models.PositiveIntegerField(default=100); obrigatorio=models.BooleanField(default=False); ativo=models.BooleanField(default=True); video_url=models.URLField(blank=True); nota_minima=models.PositiveSmallIntegerField(default=70)
    def __str__(self): return self.titulo

class TrilhaColaborador(BaseEmpresa):
    colaborador=models.ForeignKey(Colaborador,on_delete=models.CASCADE,related_name='trilhas'); treinamento=models.ForeignKey(Treinamento,on_delete=models.CASCADE)
    status=models.CharField(max_length=20,choices=[('pendente','Pendente'),('andamento','Em andamento'),('concluido','Concluído')],default='pendente')
    nota=models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True); concluido_em=models.DateTimeField(null=True,blank=True); inicio=models.DateField(null=True,blank=True); prazo=models.DateField(null=True,blank=True)
    class Meta: unique_together=[('colaborador','treinamento')]

class TentativaJogo(BaseEmpresa):
    colaborador=models.ForeignKey(Colaborador,on_delete=models.CASCADE,related_name='tentativas'); jogo=models.CharField(max_length=40)
    pontuacao=models.PositiveIntegerField(default=0); total=models.PositiveIntegerField(default=0); detalhes=models.JSONField(default=dict,blank=True)

class RegistroLGPD(BaseEmpresa):
    TIPO=[('consentimento','Consentimento'),('privacidade','Ciência de privacidade'),('treinamento','Treinamento LGPD'),('solicitacao','Solicitação de titular')]
    tipo=models.CharField(max_length=20,choices=TIPO); usuario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)
    finalidade=models.CharField(max_length=255,blank=True); base_legal=models.CharField(max_length=120,blank=True); status=models.CharField(max_length=30,default='registrado')
    detalhes=models.TextField(blank=True); ip_hash=models.CharField(max_length=64,blank=True); registrado_em=models.DateTimeField(auto_now_add=True)

class AtividadeTratamento(BaseEmpresa):
    nome=models.CharField(max_length=180); area=models.CharField(max_length=120,blank=True); finalidade=models.TextField()
    base_legal=models.CharField(max_length=120); titulares=models.CharField(max_length=180,blank=True); dados_pessoais=models.TextField(blank=True)
    compartilhamentos=models.TextField(blank=True); retencao=models.CharField(max_length=120,blank=True); medidas_seguranca=models.TextField(blank=True)
    responsavel=models.CharField(max_length=120,blank=True); risco=models.CharField(max_length=10,choices=[('baixo','Baixo'),('medio','Médio'),('alto','Alto')],default='medio')
    ativo=models.BooleanField(default=True)
    def __str__(self): return self.nome

class SolicitacaoTitular(BaseEmpresa):
    TIPO=[('acesso','Acesso'),('correcao','Correção'),('eliminacao','Eliminação'),('portabilidade','Portabilidade'),('oposicao','Oposição/ revisão')]
    protocolo=models.CharField(max_length=40,blank=True); titular=models.CharField(max_length=160); contato=models.CharField(max_length=160,blank=True)
    tipo=models.CharField(max_length=20,choices=TIPO); descricao=models.TextField(blank=True); prazo=models.DateField(null=True,blank=True)
    status=models.CharField(max_length=20,choices=[('recebida','Recebida'),('analise','Em análise'),('respondida','Respondida'),('encerrada','Encerrada')],default='recebida')
    resposta=models.TextField(blank=True)

class IncidentePrivacidade(BaseEmpresa):
    titulo=models.CharField(max_length=180); ocorrido_em=models.DateTimeField(); descricao=models.TextField(); dados_afetados=models.TextField(blank=True)
    titulares_afetados=models.PositiveIntegerField(default=0); risco=models.CharField(max_length=10,choices=[('baixo','Baixo'),('medio','Médio'),('alto','Alto')],default='medio')
    contencao=models.TextField(blank=True); avaliacao_anpd=models.TextField(blank=True); status=models.CharField(max_length=20,choices=[('aberto','Aberto'),('contido','Contido'),('investigacao','Investigação'),('encerrado','Encerrado')],default='aberto')

class ConquistaColaborador(BaseEmpresa):
    colaborador=models.ForeignKey(Colaborador,on_delete=models.CASCADE,related_name='conquistas'); codigo=models.CharField(max_length=60); titulo=models.CharField(max_length=120); descricao=models.CharField(max_length=255,blank=True); concedida_em=models.DateTimeField(auto_now_add=True)
    class Meta: unique_together=[('colaborador','codigo')]


class PontuacaoAtividade(BaseEmpresa):
    colaborador=models.ForeignKey(Colaborador,on_delete=models.CASCADE,related_name='pontuacoes_atividade')
    categoria=models.CharField(max_length=30,choices=[('jogo','Jogo'),('qualidade','Ferramenta da qualidade'),('treinamento','Treinamento'),('melhoria','Melhoria contínua'),('reconhecimento','Reconhecimento')])
    ferramenta=models.CharField(max_length=60,blank=True); titulo=models.CharField(max_length=180); pontos=models.PositiveIntegerField(default=0); detalhes=models.JSONField(default=dict,blank=True)
    criado_em=models.DateTimeField(auto_now_add=True)

class Reconhecimento(BaseEmpresa):
    colaborador=models.ForeignKey(Colaborador,on_delete=models.CASCADE,related_name='reconhecimentos')
    concedido_por=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)
    titulo=models.CharField(max_length=120); mensagem=models.CharField(max_length=500,blank=True); pontos=models.PositiveIntegerField(default=25); criado_em=models.DateTimeField(auto_now_add=True)

class Notificacao(BaseEmpresa):
    usuario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='notificacoes_gestao')
    titulo=models.CharField(max_length=160); mensagem=models.CharField(max_length=500,blank=True); link=models.CharField(max_length=255,blank=True)
    lida=models.BooleanField(default=False); criado_em=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-criado_em']

class ComentarioTarefa(BaseEmpresa):
    tarefa=models.ForeignKey(Tarefa,on_delete=models.CASCADE,related_name='comentarios'); autor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True)
    texto=models.TextField(); criado_em=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['criado_em']

class RegistroAuditoriaSistema(BaseEmpresa):
    usuario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True); acao=models.CharField(max_length=80)
    objeto=models.CharField(max_length=120,blank=True); descricao=models.CharField(max_length=500,blank=True); criado_em=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-criado_em']

class MetaEquipe(BaseEmpresa):
    titulo=models.CharField(max_length=160); setor=models.ForeignKey(Setor,on_delete=models.SET_NULL,null=True,blank=True); descricao=models.TextField(blank=True)
    meta_pontos=models.PositiveIntegerField(default=500); inicio=models.DateField(null=True,blank=True); fim=models.DateField(null=True,blank=True); ativa=models.BooleanField(default=True)

class EtapaTreinamento(BaseEmpresa):
    treinamento=models.ForeignKey(Treinamento,on_delete=models.CASCADE,related_name='etapas')
    ordem=models.PositiveIntegerField(default=1); titulo=models.CharField(max_length=180); descricao=models.TextField(blank=True)
    video_url=models.URLField(blank=True); material=models.FileField(upload_to='gestao/treinamentos/',blank=True,null=True)
    pergunta=models.CharField(max_length=300,blank=True); resposta_esperada=models.CharField(max_length=300,blank=True)
    pontos=models.PositiveIntegerField(default=20); obrigatoria=models.BooleanField(default=True)
    class Meta: ordering=['treinamento','ordem']; unique_together=[('treinamento','ordem')]
    def __str__(self): return f'{self.treinamento} • {self.ordem}. {self.titulo}'

class ProgressoEtapa(BaseEmpresa):
    colaborador=models.ForeignKey(Colaborador,on_delete=models.CASCADE,related_name='progresso_etapas')
    etapa=models.ForeignKey(EtapaTreinamento,on_delete=models.CASCADE,related_name='progressos')
    concluida=models.BooleanField(default=False); resposta=models.CharField(max_length=500,blank=True); concluida_em=models.DateTimeField(null=True,blank=True)
    class Meta: unique_together=[('colaborador','etapa')]

class PreferenciaNotificacao(BaseEmpresa):
    usuario=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='preferencias_alertas')
    email_avisos=models.BooleanField(default=True); aviso_7_dias=models.BooleanField(default=True); aviso_1_dia=models.BooleanField(default=True); aviso_atraso=models.BooleanField(default=True)

class AlertaEnviado(BaseEmpresa):
    usuario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE); chave=models.CharField(max_length=180); canal=models.CharField(max_length=20,default='plataforma')
    enviado_em=models.DateTimeField(auto_now_add=True)
    class Meta: unique_together=[('loja','usuario','chave','canal')]
