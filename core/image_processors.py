from PIL import Image
from django.conf import settings
from easy_thumbnails.signals import saved_file
import logging
logger = logging.getLogger("default")

def watermark_processor(image, **kwargs):
    """
    Add watermark to the source image.
    """
    logger.debug("watermark_processor")
    try:
        wm_image_path = settings.YZ_WATERMARK_IMAGE
        wm_image = Image.open(wm_image_path)
    except:
        logger.exception("watermark_processor: error")
        pass
    else:
        ix, iy = image.size
        wx, wy = wm_image.size
        if ix < wx or iy < wy:
            wm_image = wm_image.thumbnail( (ix, iy), Image.ANTIALIAS)
        tx, ty = (ix-wx) / 2, (iy-wy) / 2
        image.paste(wm_image, (tx, ty), wm_image)
    return image

def add_watermark(sender, fieldfile, **kwargs):
    """ Add watermark to easy_thumbnails fields' images (on uploading) """
    logger.debug("add_watermark")
    try:
        wm_image_path = settings.YZ_WATERMARK_IMAGE
    except AttributeError:
        logger.debug("add_watermark: no watermark file defined")
        return

    try:
        wm_image = Image.open(wm_image_path)
        image = Image.open(fieldfile.path)
        ix, iy = image.size
        wx, wy = wm_image.size
        if ix < wx or iy < wy:
            wm_image.thumbnail( (ix, iy), Image.ANTIALIAS)
            wx, wy = wm_image.size
        tx, ty = (ix-wx) / 2, (iy-wy) / 2
        image.paste(wm_image, (tx, ty), wm_image)
        image.save(fieldfile.path)
    except:
        logger.exception("add_watermark: error: failed to add watermark")
    else:
        logger.debug("add_watermark: written file %s", fieldfile.path)
saved_file.connect(add_watermark)


