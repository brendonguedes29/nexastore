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
    class Meta:
        model=Processo; exclude=['loja']
        labels={'nome':'Nome do processo','codigo':'Código / identificação','objetivo':'Para que este processo existe?','responsavel':'Responsável pelo processo','entradas':'O que entra no processo?','saidas':'O que o processo entrega?','riscos':'Principais riscos / pontos de atenção','setor':'Área responsável','status':'Situação atual'}
        help_texts={'entradas':'Ex.: pedido do cliente, matéria-prima, informação.','saidas':'Ex.: produto acabado, relatório, serviço entregue.','riscos':'Liste riscos que podem impedir o resultado esperado.'}
class IndicadorForm(StyledModelForm):
    class Meta:
        model=Indicador; exclude=['loja']
        labels={'nome':'O que você quer acompanhar?','processo':'Processo relacionado','unidade':'Unidade de medida','meta':'Meta desejada','sentido':'Quando o resultado é melhor?','periodicidade':'Com que frequência medir?','responsavel':'Responsável (texto)','responsavel_colaborador':'Responsável da equipe','inicio':'Início do acompanhamento','previsao_conclusao':'Data-alvo (se houver)','ativo':'Indicador ativo'}
class MedicaoForm(StyledModelForm):
    class Meta: model=MedicaoIndicador; exclude=['loja']
class PlanoAcaoForm(StyledModelForm):
    class Meta:
        model=PlanoAcao; exclude=['loja']
        labels={'titulo':'Nome da ação','origem':'De onde surgiu esta ação?','o_que':'O que será feito?','por_que':'Por que precisa ser feito?','onde':'Onde será feito?','quem':'Quem será responsável?','quando':'Quando deve estar pronto?','como':'Como será executado?','quanto':'Quanto vai custar?','status':'Andamento','prioridade':'Prioridade'}
class NCForm(StyledModelForm):
    class Meta:
        model=NaoConformidade; exclude=['loja']
        labels={'codigo':'Código da ocorrência','titulo':'O que aconteceu?','descricao':'Descreva a não conformidade e a evidência','processo':'Processo afetado','causa_raiz':'Qual foi a causa raiz identificada?','correcao':'Correção / ação corretiva','responsavel':'Responsável pela tratativa','prazo':'Prazo para resolver','status':'Etapa da tratativa','severidade':'Severidade (1 a 5)'}
class DocumentoForm(StyledModelForm):
    class Meta:
        model=DocumentoGestao; exclude=['loja','aprovado']
        labels={'codigo':'Código do documento','titulo':'Título do documento','tipo':'Tipo','versao':'Versão atual','responsavel':'Proprietário / responsável','arquivo':'Arquivo','conteudo':'Resumo / conteúdo controlado','status':'Situação documental','data_emissao':'Data de emissão','proxima_revisao':'Próxima revisão'}
class AuditoriaForm(StyledModelForm):
    class Meta:
        model=Auditoria; exclude=['loja','data']
        labels={'titulo':'Nome da auditoria','escopo':'O que será auditado?','auditor':'Auditor responsável','inicio':'Data de início','previsao_conclusao':'Previsão de conclusão','conclusao':'Conclusão real','status':'Situação','resultado':'Constatações, evidências e resultado'}
class ISOForm(StyledModelForm):
    class Meta: model=RequisitoISO; exclude=['loja']
class FMEAForm(StyledModelForm):
    class Meta:
        model=RiscoFMEA; exclude=['loja']
        labels={'processo':'1. Qual processo será analisado?','modo_falha':'2. O que pode dar errado? (modo de falha)','efeito':'3. Se falhar, qual é a consequência? (efeito)','causa':'4. Por que isso pode acontecer? (causa)','severidade':'5. Severidade do efeito (1–10)','ocorrencia':'6. Chance de acontecer (1–10)','deteccao':'7. Dificuldade de detectar antes do efeito (1–10)','controles_atuais':'8. Como a empresa previne/detecta hoje?','acao':'9. Ação recomendada','responsavel_acao':'Responsável pela ação','prazo_acao':'Prazo','status_acao':'Andamento da ação','severidade_pos':'Severidade após ação','ocorrencia_pos':'Ocorrência após ação','deteccao_pos':'Detecção após ação'}
class ProducaoForm(StyledModelForm):
    class Meta:
        model=RegistroProducao; exclude=['loja']
        labels={'data':'Data da medição','linha':'Linha / célula de produção','equipamento':'Equipamento principal (opcional)','produto':'Produto / família produzida','turno':'Turno / período','tempo_planejado':'Tempo planejado para produzir (min)','tempo_operando':'Tempo realmente operando (min)','quantidade_total':'Peças produzidas no período (total)','quantidade_boa':'Peças boas na primeira aprovação','ciclo_ideal':'Tempo ideal para produzir 1 peça (min/peça)'}
        help_texts={'tempo_planejado':'Ex.: turno de 480 min menos almoço e parada programada.','tempo_operando':'Tempo planejado menos quebra, setup não previsto e outras paradas não planejadas.','quantidade_total':'Inclua boas, refugadas e retrabalhadas produzidas no período.','quantidade_boa':'Somente peças aprovadas sem retrabalho. Deve ser menor ou igual ao total.','ciclo_ideal':'Ex.: se a melhor condição sustentável é 30 s/peça, informe 0,5 min/peça.'}
class SetorForm(StyledModelForm):
    class Meta:
        model=Setor; exclude=['loja']
        labels={'nome':'Nome do setor / área','descricao':'Responsabilidade da área','gestor':'Gestor responsável','ativo':'Área ativa'}
class TarefaForm(StyledModelForm):
    class Meta:
        model=Tarefa; exclude=['loja']
        labels={'titulo':'O que precisa ser feito?','descricao':'Descrição / critério de conclusão','setor':'Área','responsavel':'Responsável','inicio':'Data de início','fim':'Prazo','status':'Etapa','prioridade':'Prioridade'}
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
    class Meta:
        model=Treinamento
        fields=['titulo','descricao','categoria','pontos','nota_minima','obrigatorio','ativo']
        labels={'titulo':'Título','descricao':'Descrição','categoria':'Categoria','pontos':'Pontos de referência','nota_minima':'Nota mínima geral (%)','obrigatorio':'Obrigatório','ativo':'Ativo'}
class LGPDForm(StyledModelForm):
    class Meta: model=RegistroLGPD; exclude=['loja','usuario','ip_hash']
class AtividadeTratamentoForm(StyledModelForm):
    class Meta:
        model=AtividadeTratamento; exclude=['loja']
        labels={'nome':'Atividade que usa dados pessoais','area':'Área responsável','finalidade':'Para que esses dados são usados?','base_legal':'Qual base legal sustenta o tratamento?','titulares':'De quem são os dados?','dados_pessoais':'Quais dados são utilizados?','compartilhamentos':'Com quem os dados são compartilhados?','retencao':'Por quanto tempo ficam armazenados?','medidas_seguranca':'Como os dados são protegidos?','responsavel':'Dono do tratamento','risco':'Nível de risco','ativo':'Tratamento ativo'}
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
