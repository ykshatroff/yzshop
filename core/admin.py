from django.contrib import admin

from .models import Country
from .models import Shop
from .models import StaticBlock

admin.site.register(Country)
admin.site.register(Shop)
admin.site.register(StaticBlock)