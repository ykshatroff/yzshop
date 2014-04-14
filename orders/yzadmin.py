
from django import forms
#from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _


from .models import DeliveryMethod
from .models import PaymentMethod
from .models import Order

from yz.admin.dispatchers import ModelDispatcher
from yz.admin.dispatchers import PageDispatcherMixin
from yz.admin.dispatchers import TabsDispatcher
from yz.admin.dispatchers import BadParameterException
from yz.admin.dispatchers import ItemNotFoundException

#from yz.admin.forms import CalendarWidget
from yz.admin.forms import TinyMCEWidget

# ### DeliveryMethod forms
class DeliveryMethodAddForm(ModelForm):
    class Meta:
        model = DeliveryMethod
        fields = ('name', 'slug')

class DeliveryMethodDataForm(ModelForm):
    class Meta:
        model = DeliveryMethod
        widgets = {
            'description': TinyMCEWidget,
        }

# ### PaymentMethod forms
class PaymentMethodAddForm(ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ('name', 'slug')


class PaymentMethodDataForm(ModelForm):
    class Meta:
        model = PaymentMethod
        widgets = {
            'description': TinyMCEWidget,
        }



# ### Dispatchers
class DeliveryMethodDispatcher(ModelDispatcher, PageDispatcherMixin):
    """
    The DeliveryMethod model dispatcher for YZ management `console`
    """
    add_form_class = DeliveryMethodAddForm
    form_class = DeliveryMethodDataForm

class PaymentMethodDispatcher(ModelDispatcher, PageDispatcherMixin):
    """
    The PaymentMethod model dispatcher for YZ management `console`
    """
    add_form_class = PaymentMethodAddForm
    form_class = PaymentMethodDataForm


class OrderDispatcher(TabsDispatcher, PageDispatcherMixin):
    """
    The Orders model dispatcher for YZ management `console`
    NOTE: no adding, no forms
    """
    tabs_descriptor = (
        ('data', _('Data'), None),
        ('products', _('Products'), None),
        ('status', _('status'), None),
    )

    def index_view(self, request):
        """
        Index view of the order management section
        Some statistics
        """
        #from django.db.models import Count, Sum
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT status, COUNT(*), SUM(total)
            FROM orders_order
            GROUP BY status
            ORDER BY status
        """)
        res = cursor.fetchall()
        orders_stat = []
        total = 0
        number = 0
        for status, count, sum in res:
            number += count
            total += sum
            try:
                st = (status, Order.STATUS_LABELS[status], count, sum)
            except KeyError:
                pass
            else:
                orders_stat.append(st)
        context = {
            'orders_stat': orders_stat,
            'number': number,
            'total': total,
        }
        return self.render( 'index', request, context )


    def data_view(self, request, item_id):
        """
        Order data: list of field-value pairs
        """
        item = self.get_object(item_id)
        fields = ('number', 'date_submitted',
            'customer_name',
            'customer_company_name',
            'customer_email',
            'customer_phone',
            'delivery_method_name', 'delivery_cost',
            'payment_method_name', 'payment_cost',
            'value', 'total',
        )
        order_fields = [(item._meta.get_field(f).verbose_name,
                getattr(item, f)) for f in fields]
        status = (item._meta.get_field("status").verbose_name,
                item.get_text_status())
        order_fields.insert(0, status)
        context = {
            'item': item,
            'order_fields': order_fields,
        }
        return self.render_tab('data', request, context)

    def products_view(self, request, item_id):
        """
        List of ordered products (variants)
        """
        item = self.get_object(item_id)
        context = {
            'item': item,
            'order_items': item.items.all(),
        }
        return self.render_tab('products', request, context)

    def status_view(self, request, item_id):
        """
        List of status dates
        """
        item = self.get_object(item_id)
        fields = (
            'date_submitted',
            'date_paid',
            'date_sent',
            'date_cancelled',
            'date_closed',
        )
        order_fields = [(item._meta.get_field(f).verbose_name,
                getattr(item, f)) for f in fields]
        context = {
            'item': item,
            'order_fields': order_fields,
        }
        return self.render_tab('status', request, context)

    def change_status_view(self, request, item_id):
        """
        Change order status
        """
        item = self.get_object(item_id)
        try:
            new_status = int(request.GET['status'])
        except:
            raise BadParameterException('status')

        try:
            item.set_status(new_status)
        except ValueError:
            self.add_message(request, self.MSG_ERROR)
        else:
            self.add_message(request, self.MSG_UPDATED)
        return self.redirect('status', request, item.id)


def setup(dispatcher):
    dispatcher.register(DeliveryMethodDispatcher(DeliveryMethod), menuitem='shop')
    dispatcher.register(PaymentMethodDispatcher(PaymentMethod), menuitem='shop')
    dispatcher.register(OrderDispatcher(Order), menuitem='orders')

