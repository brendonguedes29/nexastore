from decimal import Decimal
from django.db import migrations, models

def atualizar_preco(apps,schema_editor):
    Loja=apps.get_model('lojas','Loja')
    Loja.objects.filter(valor_licenca=Decimal('59.90')).update(valor_licenca=Decimal('199.00'))

class Migration(migrations.Migration):
    dependencies=[('lojas','0013_loja_cobranca_automatica_ativa_and_more')]
    operations=[
        migrations.AlterField(model_name='loja',name='valor_licenca',field=models.DecimalField(decimal_places=2,default=199.00,max_digits=10)),
        migrations.RunPython(atualizar_preco,migrations.RunPython.noop),
    ]
