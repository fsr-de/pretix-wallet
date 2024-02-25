from django.views import View


class CustomerLoginReturnView(View):
    def get(self, request, *args, **kwargs):
        return "Customer login return view"
