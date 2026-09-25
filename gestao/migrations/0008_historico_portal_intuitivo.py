from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('gestao','0007_aprendizagem_prazos')]
    operations=[
        migrations.AddField(model_name='processo',name='setor',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='processos',to='gestao.setor')),
        migrations.AddField(model_name='projetoqualidade',name='processo',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='analises_qualidade',to='gestao.processo')),
        migrations.AddField(model_name='projetoqualidade',name='setor',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='analises_qualidade',to='gestao.setor')),
        migrations.AddField(model_name='projetoqualidade',name='concluido_em',field=models.DateTimeField(blank=True,null=True)),
    ]
