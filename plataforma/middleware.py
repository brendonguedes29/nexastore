from lojas.models import Loja

class LojaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0]

        loja = Loja.objects.filter(dominio=host).first()

        request.loja = loja

        return self.get_response(request)