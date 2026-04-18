class SubdominioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        request.loja = None

        from lojas.models import Loja

        loja = Loja.objects.filter(dominio=host).first()

        if not loja and host.endswith(".nexastoreofficial.com.br"):
            subdominio = host.replace(".nexastoreofficial.com.br", "").strip()

            if subdominio and subdominio != "www":
                loja = Loja.objects.filter(slug=subdominio).first()

        request.loja = loja

        return self.get_response(request)