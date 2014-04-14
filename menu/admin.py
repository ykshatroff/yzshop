from django.contrib import admin

from .models import MenuGroup
from .models import MenuItem

admin.site.register(MenuGroup)
admin.site.register(MenuItem)