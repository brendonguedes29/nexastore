class SubdominioMiddleware:
    def _init_(self, get_response):
        self.get_response = get_response

    def _call_(self, request):
        host = request.get_host().split(":")[0].lower()
        request.loja = None

        from lojas.models import Loja

        if request.path.startswith((
            "/admin",
            "/login",
            "/painel",
            "/entrar",
            "/criar-loja",
        )):
            return self.get_response(request)

        loja = Loja.objects.filter(dominio=host).first()

        if not loja and host.endswith(".nexastoreofficial.com.br"):
            subdominio = host.replace(".nexastoreofficial.com.br", "")

            if subdominio and subdominio != "www":
                loja = Loja.objects.filter(slug=subdominio).first()

        request.loja = loja

        return self.get_response(request)