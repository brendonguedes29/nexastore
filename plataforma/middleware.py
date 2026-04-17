class SubdominioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()

        if host == "nexastoreofficial.com.br" or host.startswith("www."):
            request.loja = None
        else:
            from lojas.models import Loja
            request.loja = Loja.objects.filter(slug=host.split(".")[0]).first()

        response = self.get_response(request)
        return response