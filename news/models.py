from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from datetime import datetime

from easy_thumbnails.fields import ThumbnailerImageField

from yz.core.models import MetaInfoModel

from .managers import NewsManager

class News(MetaInfoModel):
    """
    News Entry.
    The `name` field is actually the news title, but naming it `title` would imply
        some modifications we now choose to avoid.
    """
    name = models.CharField(max_length=120, verbose_name=_(u'title'))
    slug = models.SlugField(max_length=120, verbose_name=_(u'slug'), help_text=_(u'Auto generated from title'))
    publish = models.BooleanField(verbose_name=_(u'publish'), default=True, db_index=True)
    date_created = models.DateField(verbose_name=_(u'date'), default=datetime.now)
    image = ThumbnailerImageField(verbose_name=_(u'image'), upload_to="images/news",
            blank=True, null=True)
    body = models.TextField(verbose_name=_(u'text'))

    objects = NewsManager()

    @property
    def title(self):
        return self.name

    @property
    def text(self):
        return self.body

    @models.permalink
    def get_absolute_url(self):
        return ('yz_news_entry', (), {
            'slug': self.slug
        })

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.date_created)

    class Meta:
        ordering = ('-date_created','-id')
        get_latest_by = 'date_created'
        verbose_name = _(u'news item')
        verbose_name_plural = _(u'news items')

    @classmethod
    def get_last_news(cls, limit=3):
        """
        Get the list of 'last news' to display on some pages
        TODO caching
        """
        return cls.objects.get_latest_news(limit)
        #return cls.objects.all()[:limit]
