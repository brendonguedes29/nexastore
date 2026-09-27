from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('gestao','0014_workspace_prazos_status_cores'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[migrations.AddField(model_name='projetoqualidade',name='criado_por',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='analises_qualidade_criadas',to=settings.AUTH_USER_MODEL))]
