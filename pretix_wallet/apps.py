from django.utils.translation import gettext_lazy

from . import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    default = True
    name = "pretix_wallet"
    verbose_name = "Wallet"

    class PretixPluginMeta:
        name = gettext_lazy("Wallet")
        author = "Your name"
        description = gettext_lazy("A user-based wallet based on pretix giftcards")
        visible = True
        version = __version__
        category = "PAYMENT"
        compatibility = "pretix>=2.7.0"

    def ready(self):
        from . import signals  # NOQA
