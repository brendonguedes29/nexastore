from django.contrib import admin
from .models import *
for m in [Processo,Indicador,MedicaoIndicador,PlanoAcao,NaoConformidade,DocumentoGestao,Auditoria,RequisitoISO,RiscoFMEA,RegistroProducao,IdeiaMelhoria]:
    try: admin.site.register(m)
    except admin.sites.AlreadyRegistered: pass
