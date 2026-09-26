from django import forms
from .models import *

class StyledModelForm(forms.ModelForm):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class','field')
            if isinstance(f, forms.DateField): f.widget=forms.DateInput(attrs={'class':'field','type':'date'})
            elif isinstance(f, forms.DateTimeField): f.widget=forms.DateTimeInput(attrs={'class':'field','type':'datetime-local'})
            elif isinstance(f.widget, forms.Textarea): f.widget.attrs.setdefault('rows',4)

class ProcessoForm(StyledModelForm):
    class Meta: model=Processo; exclude=['loja']
class IndicadorForm(StyledModelForm):
    class Meta: model=Indicador; exclude=['loja']
class MedicaoForm(StyledModelForm):
    class Meta: model=MedicaoIndicador; exclude=['loja']
class PlanoAcaoForm(StyledModelForm):
    class Meta: model=PlanoAcao; exclude=['loja']
class NCForm(StyledModelForm):
    class Meta: model=NaoConformidade; exclude=['loja']
class DocumentoForm(StyledModelForm):
    class Meta: model=DocumentoGestao; exclude=['loja']
class AuditoriaForm(StyledModelForm):
    class Meta: model=Auditoria; exclude=['loja']
class ISOForm(StyledModelForm):
    class Meta: model=RequisitoISO; exclude=['loja']
class FMEAForm(StyledModelForm):
    class Meta: model=RiscoFMEA; exclude=['loja']
class ProducaoForm(StyledModelForm):
    class Meta: model=RegistroProducao; exclude=['loja']
class SetorForm(StyledModelForm):
    class Meta: model=Setor; exclude=['loja']
class TarefaForm(StyledModelForm):
    class Meta: model=Tarefa; exclude=['loja']
class NotaForm(StyledModelForm):
    class Meta:
        model=NotaWorkspace; exclude=['loja','autor','concluido_em']
        labels={'titulo':'Título','conteudo':'Nota','setor':'Setor','cor':'Cor do marcador','fixada':'Fixar nota','inicio':'Data de início','previsao':'Previsão de conclusão','status':'Status'}
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.fields['cor'].widget=forms.Select(choices=NotaWorkspace.CORES,attrs={'class':'field'})

class ProjetoQualidadeForm(StyledModelForm):
    class Meta: model=ProjetoQualidade; exclude=['loja','dados']
class TreinamentoForm(StyledModelForm):
    class Meta: model=Treinamento; exclude=['loja']
class LGPDForm(StyledModelForm):
    class Meta: model=RegistroLGPD; exclude=['loja','usuario','ip_hash']
class AtividadeTratamentoForm(StyledModelForm):
    class Meta: model=AtividadeTratamento; exclude=['loja']
class SolicitacaoTitularForm(StyledModelForm):
    class Meta: model=SolicitacaoTitular; exclude=['loja','protocolo']
class IncidentePrivacidadeForm(StyledModelForm):
    class Meta: model=IncidentePrivacidade; exclude=['loja']
class PerfilColaboradorForm(StyledModelForm):
    class Meta:
        model=Colaborador; fields=['foto','titulo_perfil','bio','email_notificacoes','perfil_visivel','ranking_visivel','mostrar_conquistas']
        widgets={'bio':forms.Textarea(attrs={'rows':4,'maxlength':500})}
class ReconhecimentoForm(StyledModelForm):
    class Meta: model=Reconhecimento; exclude=['loja','concedido_por']
class MetaEquipeForm(StyledModelForm):
    class Meta: model=MetaEquipe; exclude=['loja']
class EtapaTreinamentoForm(StyledModelForm):
    class Meta: model=EtapaTreinamento; exclude=['loja','treinamento']
class TrilhaColaboradorForm(StyledModelForm):
    class Meta: model=TrilhaColaborador; exclude=['loja','status','nota','concluido_em']
class PreferenciaNotificacaoForm(StyledModelForm):
    class Meta: model=PreferenciaNotificacao; exclude=['loja','usuario']
