class ConsentPagePrivacyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path == "/" or request.path.startswith(("/confirm/", "/unsubscribe/")):
            response["Cache-Control"] = "no-store"
            # Keep same-origin form POSTs compatible with Django CSRF checks.
            # External destinations must not receive token URLs as referrers.
            response["Referrer-Policy"] = "same-origin"
        return response
