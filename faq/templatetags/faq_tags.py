from django import template
register = template.Library()

from ..forms import QuestionForm

@register.inclusion_tag('faq/tags/question-form.html', takes_context=True)
def question_form(context):
    form = context.get('form', QuestionForm())
    return {
        'form': form,
        }
