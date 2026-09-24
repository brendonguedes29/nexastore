from django import forms
from .models import *

class StyledModelForm(forms.ModelForm):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        for f in self.fields.values(): f.widget.attrs.setdefault('class','field')

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
