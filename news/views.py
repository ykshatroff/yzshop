# django imports
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render_to_response
from django.template import RequestContext

# module imports
from .models import News


def index_view(request):
    """
    The index view for FAQ
    """
    return page_view(request, page_number=1)

def page_view(request, page_number=1, template_name="news/list.html"):
    """
    Pagination view
    """
    try:
        page = News.objects.get_page(page_number)
    except InvalidPage:
        page = News.objects.get_page(1)

    context = {
        'page': page,
    }
    return render_to_response(template_name, RequestContext(request, context))

