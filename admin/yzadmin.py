from .models import UploadedImage
from .forms import TinyMCEImageUploadForm

from yz.admin.dispatchers import PageDispatcherMixin
from yz.admin.dispatchers import ModelDispatcher

class UploadImageDispatcher(ModelDispatcher, PageDispatcherMixin):
    """
    Dispatcher for UploadedImage images
    """
    model = UploadedImage

    def upload_view(self, request):
        """
        Upload an image (e.g. via TinyMCE)
        """
        item = None
        form_class = TinyMCEImageUploadForm
        if request.method == "POST":
            form = form_class(data=request.POST, files=request.FILES)
            if form.is_valid():
                item = form.save()
                self.add_message(request, self.MSG_ADDED)
                #return self.redirect('edit', request, item.id)
        else:
            form = form_class()
        context = {
            'form': form,
            'item': item,
            }
        return self.render( 'upload', request, context )


def setup(dispatcher):
    dispatcher.register(UploadImageDispatcher(), menuitem='other')
