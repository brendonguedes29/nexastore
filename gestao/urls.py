from django.urls import path
from . import views
urlpatterns=[
 path('',views.dashboard,name='gestao_dashboard'),
 path('processos/',views.processos,name='gestao_processos'),
 path('indicadores/',views.indicadores,name='gestao_indicadores'),
 path('planos-acao/',views.planos,name='gestao_planos'),
 path('nao-conformidades/',views.nao_conformidades,name='gestao_nc'),
 path('documentos/',views.documentos,name='gestao_documentos'),
 path('auditorias/',views.auditorias,name='gestao_auditorias'),
 path('iso-9001/',views.iso,name='gestao_iso'),
 path('fmea/',views.fmea,name='gestao_fmea'),
 path('producao-oee/',views.producao,name='gestao_producao'),
 path('ferramentas/',views.ferramentas,name='gestao_ferramentas'),
 path('academia/',views.academia,name='gestao_academia'),
]
