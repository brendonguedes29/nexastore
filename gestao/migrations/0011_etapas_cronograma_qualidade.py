from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('gestao','0010_indicador_responsavel_colaborador')]
    operations=[
        migrations.CreateModel(
            name='EtapaProjetoQualidade',
            fields=[
                ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
                ('criado_em',models.DateTimeField(auto_now_add=True)),('atualizado_em',models.DateTimeField(auto_now=True)),
                ('ordem',models.PositiveIntegerField(default=1)),('titulo',models.CharField(max_length=180)),('descricao',models.TextField(blank=True)),
                ('inicio',models.DateField(blank=True,null=True)),('previsao',models.DateField(blank=True,null=True)),('concluido_em',models.DateTimeField(blank=True,null=True)),
                ('status',models.CharField(choices=[('nao_iniciada','Não iniciada'),('andamento','Em andamento'),('bloqueada','Bloqueada'),('concluida','Concluída')],default='nao_iniciada',max_length=20)),
                ('observacoes',models.TextField(blank=True)),('evidencia',models.FileField(blank=True,null=True,upload_to='gestao/evidencias_etapas/')),('pontos',models.PositiveIntegerField(default=10)),
                ('loja',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='lojas.loja')),
                ('projeto',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='etapas_cronograma',to='gestao.projetoqualidade')),
                ('responsavel',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='etapas_qualidade',to='gestao.colaborador')),
            ], options={'ordering':['projeto','ordem','id']}
        )
    ]
