class SubdominioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        request.loja = None

        from lojas.models import Loja

        # 🔥 IGNORA rotas administrativas e login
        if request.path.startswith((
            "/admin",
            "/login",
            "/painel",
            "/entrar",
            "/criar-loja",
        )):
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