from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('gestao','0019_etapatreinamento_slides')]
    operations=[
        migrations.AddField(model_name='etapatreinamento',name='max_tentativas',field=models.PositiveSmallIntegerField(default=3,help_text='0 = tentativas ilimitadas')),
        migrations.CreateModel(
            name='TentativaAvaliacao',
            fields=[
                ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
                ('criado_em',models.DateTimeField(auto_now_add=True)),('atualizado_em',models.DateTimeField(auto_now=True)),
                ('numero',models.PositiveSmallIntegerField(default=1)),('nota',models.DecimalField(decimal_places=2,default=0,max_digits=5)),
                ('acertos',models.PositiveIntegerField(default=0)),('total',models.PositiveIntegerField(default=0)),('aprovado',models.BooleanField(default=False)),
                ('respostas',models.JSONField(blank=True,default=dict)),('realizado_em',models.DateTimeField(auto_now_add=True)),
                ('colaborador',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='tentativas_avaliacao',to='gestao.colaborador')),
                ('etapa',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='tentativas_avaliacao',to='gestao.etapatreinamento')),
                ('loja',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='lojas.loja')),
            ],
            options={'ordering':['etapa','colaborador','numero'],'unique_together':{('colaborador','etapa','numero')}},
        ),
    ]
