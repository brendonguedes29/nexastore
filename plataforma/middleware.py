class SubdominioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        request.loja = None

        from lojas.models import Loja

        # 🔥 Ignora domínios principais (evita conflito com landing)
        if host in [
            "nexastoreofficial.com.br",
            "www.nexastoreofficial.com.br",
            "nexastore-xw5y.onrender.com"
        ]:
            return self.get_response(request)

        # 1. Domínio próprio
        loja = Loja.objects.filter(dominio=host).first()

        # 2. Subdomínio
        if not loja and host.endswith(".nexastoreofficial.com.br"):
            subdominio = host.replace(".nexastoreofficial.com.br", "")

            if subdominio and subdominio != "www":
                loja = Loja.objects.filter(slug=subdominio).first()

        request.loja = loja

        return self.get_response(request)