from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('gestao','0008_historico_portal_intuitivo')]
    operations=[
        migrations.AddField(model_name='colaborador',name='cpf',field=models.CharField(blank=True,max_length=14)),
        migrations.AddField(model_name='colaborador',name='status_cadastro',field=models.CharField(choices=[('aprovado','Aprovado'),('pendente','Aguardando aprovação'),('rejeitado','Rejeitado')],default='aprovado',max_length=20)),
        migrations.AddField(model_name='colaborador',name='supervisor',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='supervisionados',to='gestao.colaborador')),
        migrations.AddField(model_name='indicador',name='inicio',field=models.DateField(blank=True,null=True)),
        migrations.AddField(model_name='indicador',name='previsao_conclusao',field=models.DateField(blank=True,null=True)),
        migrations.AddField(model_name='indicador',name='concluido_em',field=models.DateTimeField(blank=True,null=True)),
        migrations.CreateModel(name='CertificadoTreinamento',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('criado_em',models.DateTimeField(auto_now_add=True)),('atualizado_em',models.DateTimeField(auto_now=True)),('codigo',models.CharField(max_length=48,unique=True)),('emitido_em',models.DateTimeField(auto_now_add=True)),('carga_horaria_minutos',models.PositiveIntegerField(default=30)),('colaborador',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='certificados',to='gestao.colaborador')),('loja',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='lojas.loja')),('treinamento',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='certificados',to='gestao.treinamento'))],options={'unique_together':{('colaborador','treinamento')}}),
    ]
