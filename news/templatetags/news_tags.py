from django import template
register = template.Library()

from ..models import News

@register.inclusion_tag('news/tags/latest-news.html', takes_context=True)
def latest_news(context, limit=3):
    """
    Display the news
    """
    news = News.get_last_news(limit)
    return {
        'latest_news': news,
    }
