from django.conf import settings
from yz.core.models import Shop


def main(request):
    """context processor for yzshop
    """
    return {
        "SHOP": request.current_shop,
    }

