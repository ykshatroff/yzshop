import logging
import re
from yz.utils import translit

class UploadFileNameMiddleware(object):
    """
    Rename uploaded files so their names contain only ASCII chars
    """
    def process_request(self, request):
        logger = logging.getLogger("default")
        #logger.debug("UploadFileNameMiddleware.process_request(%s)", request.method)
        if request.method == "POST" and request.FILES:
            logger.debug("UploadFileNameMiddleware.process_request() -> start")
            for fn, f in request.FILES.items():
                logger.debug("UploadFileNameMiddleware.process_request(): field=%s, file=%s", fn, f.name)
                new_name = translit(f.name)
                new_name = re.sub(u'\s+', '_', new_name)
                new_name = re.sub(u'[^0-9A-Za-z._-]+', '', new_name)
                f.name = new_name

class AjaxDebugMiddleware(object):
    """ Enable debugging of AJAX requests: simulate one by adding ?is_ajax=1 to GET query string """
    def process_request(self, request):
        if 'is_ajax' in request.GET:
            request.is_ajax = lambda: True
