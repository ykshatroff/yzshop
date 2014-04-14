# django imports
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django import http
from django.shortcuts import render_to_response
from django.template import RequestContext

# module imports
from .forms import QuestionForm
from .models import Question

def index_view(request):
    """
    The index view for FAQ
    """
    return page_view(request, page_number=1)

def page_view(request, page_number=1, template_name="faq/list.html"):
    """
    Pagination view
    """
    try:
        page = Question.objects.get_page(page_number)
    except InvalidPage:
        page = Question.objects.get_page(page_number=1)

    context = {
        'page': page,
    }
    return render_to_response(template_name, RequestContext(request, context))


def ask_question(request, template_name="faq/ask.html"):
    """
    Ask question: create a question submitted by user
    """
    if request.method == "POST":
        form = QuestionForm(data=request.POST)
        if form.is_valid():
            question = form.save()
            return http.HttpResponseRedirect(reverse('yz_faq_question_added'))
    else:
        form = QuestionForm()

    context = {
        'form': form,
    }
    return render_to_response(template_name, RequestContext(request, context))


def question_added(request, template_name="faq/added.html"):
    """
    The view is redirected to after successful adding of a question (in ask_question())
    """
    return render_to_response(template_name, RequestContext(request, {}))
