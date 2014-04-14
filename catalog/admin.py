from django.contrib import admin

from .models import Manufacturer
from .models import Category
from .models import Product
from .models import Property
from .models import PropertyOption
from .models import ProductPropertyValue

admin.site.register(Manufacturer)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Property)
admin.site.register(PropertyOption)
admin.site.register(ProductPropertyValue)
