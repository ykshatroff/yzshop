from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from .models import MenuGroup
from .models import MenuItem

class MenuItemDispatcherMixin(object):
    """
    Dispatcher mixin for adding menuitem management functionality
        to model dispatchers which would like to be able to link
        their items to menu items
    At present, implemented is only one-level (plain) menu management
    The target dispatcher must be instance of TabsDispatcher and
        have a 'menu' tab
    """

    MSG_ERROR_NO_GROUP = _('Menu group "%(gid)s" does not exist')

    def add_to_menu_view(self, request, item_id):
        "Add item to a menu or several menus"
        #content_type = ContentType.objects.get_for_model(item)
        if request.method == "POST":
            item = self.get_object(item_id)
            groups = request.POST.getlist('add_menugroup')
            title = request.POST.get('title')
            for gid in groups:
                try:
                    group = MenuGroup.objects.get(id=gid)
                except MenuGroup.DoesNotExist:
                    # add message
                    self.add_message(request, self.MSG_ERROR_NO_GROUP %  dict(gid=gid))
                else:
                    try:
                        menuitem = group.items.create(title=title,
                                                  link=item.get_absolute_url(),
                                                  group=group,
                                                  content_object=item,

                                                  )
                    except:
                        self.add_message(request, self.MSG_ERROR)
                    else:
                        self.add_message(request, self.MSG_ADDED)

            #return self.redirect('menu', request, item.id)
        return self.redirect('menu', request, item_id)

    def menu_view(self, request, item_id):
        "Manage menu items for the object (tab view)"
        item = self.get_object(item_id)
        # 1. try to determine if the object is on a menu (might be several times)
        # assert there is the correct content type
        content_type = ContentType.objects.get_for_model(item)
        menuitems = MenuItem.objects.filter(content_type=content_type, object_id=item.id)
        # 2. get all groups
        menugroups = MenuGroup.objects.all()
        context = {
            'item': item,
            'menuitems': menuitems,
            'menugroups': menugroups,
        }
        return self.render_tab('menu', request, context)

    def delete_from_menu_view(self, request, item_id):
        "Delete item from menu"
        if request.method == "POST":
            item = self.get_object(item_id)
            menuitem_ids = request.POST.getlist('delete')
            menuitems = MenuItem.objects.filter(id__in=menuitem_ids)
            for mi in menuitems:
                mi.delete()
            self.add_message(request, self.MSG_UPDATED)

        return self.redirect('menu', request, item_id)
