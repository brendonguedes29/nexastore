from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("gestao", "0009_portal_cadastro_certificados_indicadores")]
    operations = [
        migrations.AddField(
            model_name="indicador",
            name="responsavel_colaborador",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="indicadores_atribuidos", to="gestao.colaborador"),
        ),
    ]
