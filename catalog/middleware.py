
from yz.core.models import Shop

class CatalogMiddleware(object):
    """
    Request phase to set up current shop and catalog
    """

    def process_request(self, request):
        request.current_shop = Shop.get_default_shop(request)
