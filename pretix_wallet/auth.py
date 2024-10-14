from django.contrib.auth.models import AnonymousUser
from pretix.base.models import Event
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


class TerminalUser(AnonymousUser):
    pass


class TerminalAuthentication(TokenAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        self.request = request
        request.event = (
            Event.objects.filter(
                slug=request.resolver_match.kwargs["event"],
                organizer__slug=request.resolver_match.kwargs["organizer"],
            )
            .select_related("organizer")
            .first()
        )
        if not request.event:
            return False
        return super().authenticate(request)

    def authenticate_credentials(self, key):
        if key and self.request.event.settings.get("payment_wallet_api_key") == key:
            return (TerminalUser(), None)
        raise AuthenticationFailed("Invalid API key")


class TerminalPermission(BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.user, TerminalUser):
            return True
        return False
