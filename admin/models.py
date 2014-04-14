import os
from django.db import models
from django.utils.translation import ugettext_lazy as _

# Create your models here.
class UploadedImage(models.Model):
    image = models.ImageField(_(u'image'), upload_to="images/uploaded",
                              height_field='height',
                              width_field='width')
    name = models.CharField(_(u"title"), max_length=100, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    height = models.IntegerField(_(u"height"), editable=False)
    width = models.IntegerField(_(u"width"), editable=False)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = "%s (%dx%d)" % (os.path.basename(self.image.file.name),
                                    self.image.width, self.image.height)
        return super(UploadedImage, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _(u'uploaded image')
        verbose_name_plural = _(u'uploaded images')
        ordering = ('name', )
