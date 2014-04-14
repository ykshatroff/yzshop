import uuid
from django.db import models
from django.utils.translation import ugettext_lazy as _
from datetime import datetime


from yz.core.models import MetaInfoModel

from .managers import QuestionManager

get_uuid = lambda: str(uuid.uuid4())


class Question(MetaInfoModel):
    """
    News Entry.
    The `name` field is actually the news title, but naming it `title` would imply
        some modifications we now choose to avoid.
    """
    name = models.CharField(max_length=120, verbose_name=_(u'title'))
    slug = models.SlugField(max_length=120, verbose_name=_(u'slug'),
            default=get_uuid,
            help_text=_(u'Auto generated from title'))
    author = models.CharField(max_length=250, verbose_name=_(u'author'), blank=True)
    author_email = models.EmailField(max_length=50, verbose_name=_(u'e-mail'), blank=True)
    publish = models.BooleanField(verbose_name=_(u'publish'), default=False, db_index=True,
        help_text=_(u'can only be enabled if answer is filled in'))
    position = models.IntegerField(_(u"position"), default=100, db_index=True)
    date_created = models.DateField(verbose_name=_(u'date'), default=datetime.now)
    question = models.TextField(verbose_name=_(u'question'))
    answer = models.TextField(verbose_name=_(u'answer'), blank=True)

    objects = QuestionManager()

    @property
    def title(self):
        return self.question

    @property
    def text(self):
        return self.answer

    @models.permalink
    def get_absolute_url(self):
        return ('yz_faq_entry', (), {
            'slug': self.slug
        })

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.date_created)

    class Meta:
        ordering = ('position', '-date_created')
        get_latest_by = 'date_created'
        verbose_name = _(u'question')
        verbose_name_plural = _(u'questions and answers')

    @classmethod
    def get_last_news(cls, limit=3):
        """
        Get the list of 'last news' to display on some pages
        TODO caching
        """
        return cls.objects.get_latest_news(limit)
        return cls.objects.all()[:limit]

    def save(self, *args, **kwargs):
        if not self.answer:
            self.publish = False
        if not self.name:
            if len(self.question) > 100:
                self.name = self.question[:100] + '...'
            else:
                self.name = self.question
        super(Question, self).save(*args, **kwargs)


