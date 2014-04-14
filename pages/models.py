from django.db import models
from django.utils.translation import ugettext_lazy as _
from datetime import datetime

from yz.core.models import MetaInfoModel
from yz.core.models import StaticBlock

class Page(MetaInfoModel):
    """
    Page Entry.
    The `name` field is actually the page title, but naming it `title` would imply
        some modifications we now choose to avoid.
    """
    name = models.CharField(max_length=120, verbose_name=_(u'title'))
    slug = models.SlugField(max_length=120, verbose_name=_(u'slug'), help_text=_(u'Auto generated from title'))
    date_created = models.DateField(verbose_name=_(u'creation date'), auto_now_add=True)
    date_updated = models.DateField(verbose_name=_(u'last modification date'), auto_now=True)
    static_block = models.ForeignKey(StaticBlock, verbose_name=_(u'static block'), blank=True, null=True)
    body = models.TextField(verbose_name=_(u'text'))

    @property
    def title(self):
        return self.name

    @property
    def text(self):
        return self.body

    @models.permalink
    def get_absolute_url(self):
        return ('yz_page', (), {
            'slug': self.slug
        })

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.slug)

    class Meta:
        ordering = ('name', )
        get_latest_by = 'date_created'
        verbose_name = _(u'page')
        verbose_name_plural = _(u'pages')
