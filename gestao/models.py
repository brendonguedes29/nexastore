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
