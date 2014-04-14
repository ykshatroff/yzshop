#import re
import logging
logger = logging.getLogger("default")

from django import forms
from django.forms.formsets import formset_factory
from django import http
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Max
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from yz.admin.dispatchers import ImageDispatcherMixin
from yz.admin.dispatchers import ModelDispatcher
from yz.admin.dispatchers import MetaDispatcherMixin
from yz.admin.dispatchers import PageDispatcherMixin
from yz.admin.dispatchers import PageDispatcher
from yz.admin.dispatchers import TabsDispatcher
from yz.admin.dispatchers import BadParameterException
from yz.admin.dispatchers import ItemNotFoundException
from yz.admin.forms import TinyMCEWidget

from .models import Category
from .models import Manufacturer
from .models import Product
from .models import ProductVariant
from .models import ProductImage
from .models import Property
from .models import PropertyOption
from .models import ProductPropertyRelation
from .models import ProductPropertyValue
from . import settings

# ### Product forms

class ProductAddForm(ModelForm):
    """
    Form for product variant adding
    """
    class Meta:
        model = Product
        fields = ('name', 'slug', )

class ProductVariantAddForm(ModelForm):
    """
    Form for product variant adding
    """
    sku = forms.CharField(label=_(u'sku'), max_length=50, required=True)
    variant_name = forms.CharField(label=_(u'variant title'), max_length=100)

    class Meta:
        model = ProductVariant
        fields = ('variant_name', 'sku', )


class ProductDataForm(ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'slug', 'active', 'sku', 'barcode',
                    'manufacturer', 'short_description', 'description')
        widgets = {
            'description': TinyMCEWidget,
        }

class ProductVariantDataForm(ModelForm):
    class Meta:
        model = ProductVariant
        fields = ('active', 'sku',
                  'own_name', 'name',
                  'variant_name',
                  'slug', 'barcode',
                  'own_manufacturer', 'manufacturer',
                  'own_short_description', 'short_description',
                  'own_description', 'description')
        widgets = {
            'description': TinyMCEWidget,
        }

def get_product_data_form(data=None, instance=None, files=None):
    """ Get a variant-aware ProductDataForm """
    #variants_enabled = settings.VARIANTS_ENABLED
    if instance.is_variant():
        form = ProductVariantDataForm(data=data, instance=instance.variant_cached, files=files)
    else:
        form = ProductDataForm(data=data, instance=instance, files=files)
    return form


class ProductDimensionsForm(ModelForm):
    class Meta:
        model = Product
        fields = ('units', 'quantity', 'length_units', 'width', 'height', 'length',
                  'weight_units', 'weight')

class ProductVariantDimensionsForm(ProductDimensionsForm):
    pass

class ProductImageForm(ModelForm):
    class Meta:
        model = ProductImage
        exclude = ('product', )


class ProductSaleForm(ModelForm):
    class Meta:
        model = Product
        fields = ('price', 'on_sale', 'sale_price')

class ProductVariantSaleForm(ProductSaleForm):
    class Meta:
        model = ProductVariant
        fields = ('own_price', 'price',
                  'own_on_sale', 'on_sale',
                  'own_sale_price', 'sale_price')

def get_product_price_form(data=None, instance=None, files=None):
    """ Get a variant-aware ProductSaleForm """
    if instance.is_variant():
        form = ProductVariantSaleForm(data=data, instance=instance.variant_cached, files=files)
    else:
        form = ProductSaleForm(data=data, instance=instance, files=files)
    return form



class ProductVariantCategoriesOverrideForm(ModelForm):
    class Meta:
        model = ProductVariant
        fields = ('own_categories', )


## ### Category forms
class CategoryAddForm(ModelForm):
    #parent = forms.IntegerField(required=False, widget=forms.HiddenInput)
    class Meta:
        model = Category
        fields = ('name', 'slug', 'parent')
        widgets = {
            'parent': forms.HiddenInput,
        }

class CategoryDataForm(ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'slug', 'active', 'short_description', )


class CategoryImagesForm(ModelForm):
    class Meta:
        model = Category
        fields = ('image', )


# ### Property forms
class PropertyDataForm(ModelForm):
    class Meta:
        model = Property

class PropertyOptionForm(ModelForm):
    class Meta:
        model = PropertyOption
        fields = ('value', )


def property_value_form_factory(property):
    value_type = property.value_type
    # if property.is_multivalue, field values are not required
    # ??? except one form
    required = not property.is_multivalue

    class _Form(forms.Form):
        if value_type == Property.VALUE_TYPE_BOOLEAN:
            YES_NO_CHOICES = (
                ('y', _('yes')),
                ('n', _('no')),
            )
            value = forms.NullBooleanField(label=_("value")) #required=False, choices=YES_NO_CHOICES
        elif value_type == Property.VALUE_TYPE_INTEGER:
            value = forms.IntegerField(label=_("value"), required=required)
        elif value_type == Property.VALUE_TYPE_DECIMAL:
            value = forms.DecimalField(label=_("value"), required=required)
        elif value_type == Property.VALUE_TYPE_OPTION:
            value = forms.ModelChoiceField(label=_("value"),
                    queryset=property.options.all(), required=required)

    return _Form

####
def _get_selected_ids(request, argname):
    """Helper function to get the list of (item) IDs that user selected"""
    idlist = request.POST.getlist(argname)
    ids = [] # the Ids selected by user
    # parse input
    for p in idlist:
        try:
            p = int(p)
        except ValueError:
            pass
        else:
            ids.append(p)
    return ids



# ### Dispatchers
# ### CategoryDispatcher


class CategoryDispatcher(TabsDispatcher, MetaDispatcherMixin):
    """
    The Category model dispatcher for YZ management `console`
    """
    add_form_class = CategoryAddForm

    tabs_descriptor = (
        ('data', _('Data'), CategoryDataForm),
        ('categories', _('Categories'), None),
        ('products', _('Products'), None),
        ('images', _('Images'), CategoryImagesForm),
    )

    def index_view(self, request):
        """
        List of the top categories, with possibility to change
        their position and active
        """
        context = {
            'top_categories': Category.objects.filter(parent=None),
        }
        return self.render('index', request, context)


    def categories_view(self, request, item_id):
        """
        List of the category's children, with possibility to change
        their position and active
        """
        item = self.get_object(item_id)
        form = self.add_form_class(initial=dict(parent=item))
        context = {
            'item': item,
            'subcategories': item.children.all(),
            'form': form,
            #'products': Product.objects.filter(categories__in=[item])
        }
        return self.render_tab('categories', request, context)


    def add_child_view(self, request, item_id):
        """
        Add a Category instance probably as a child to another category
        """
        form_class = self.add_form_class
        if request.method == "POST":
            form = form_class(data=request.POST)
            if form.is_valid():
                item = form.save()
                self.add_message(request, self.MSG_ADDED)
                return self.redirect('data', request, item.id)
        else:
            item = self.get_object(item_id)
            form = form_class(initial=dict(parent=item))
        context = {
            'parent': item,
            'form': form,
            'item': item,
            }
        return self.render( 'add', request, context )


    def products_view(self, request, item_id):
        """
        List of products in the category
        """
        item = self.get_object(item_id)
        context = {
            'item': item,
            'products': item.products.all(),
            #'products': Product.objects.filter(categories__in=[item])
        }
        return self.render_tab('products', request, context)


    def render(self, action, request, context={}):
        """
        """
        context.update({
            # 'categories': Category.objects.all(),
            'categories_tree': Category.objects.as_tree(),
        })
        return super(CategoryDispatcher, self).render(action, request, context)


class ProductDispatcher(TabsDispatcher, PageDispatcherMixin, ImageDispatcherMixin, MetaDispatcherMixin):
    """
    The Product model-specific dispatcher
    """
    MSG_ERROR_UNIQUE = _(u'One of the fields requires a unique value')

    add_form_class = ProductAddForm
    add_image_form_class = ProductImageForm
    model = Product

    tabs_descriptor = (
        ('data', _('Data'), get_product_data_form),
        ('categories', _('Categories'), None),
        ('variants', _('Variants'), {
            'disabled': not settings.VARIANTS_ENABLED,
            }),
        ('images', _('Images'), None),
        ('dimensions', _('Dimensions'), ProductDimensionsForm),
        ('properties', _('Properties'), None),
        ('stock', _('Stock'), None),
        ('sale', _('price'), get_product_price_form),
    )

    def _get_page_items(self, request, item=None):
        "For PageDispatcherMixin"
        filter_args = dict(parent=None)
        filter_by_name = request.GET.get("name")
        if filter_by_name:
            filter_args['name__istartswith'] = filter_by_name
        filter_by_category = request.GET.get("category")
        if filter_by_category:
            filter_args['categories__in'] = [category]
        return self.model.objects.filter(**filter_args)


    def properties_view(self, request, item_id):
        """
        List of properties assigned to a product
        """
        item = self.get_object(item_id)
        if not item.is_variant():
            # get list of all property objects wrapped with some attributes
            all_properties = dict((p.id, {'property': p, 'assigned': False})
                              for p in Property.objects.all())

            # get the IDs of assigned properties and mark them in all_properties
            for p_id in item.properties.values_list('id', flat=True):
                all_properties[p_id]['assigned'] = True
        else:
            # variants inherit their parents' properties
            #   which can not be unassigned nor added nor reordered
            all_properties = dict((p.id, {'property': p, 'assigned': True})
                              for p in item.parent.properties.all())

        # property values are defined on the product variant
        assigned_values = item.property_values.select_related('value_option').all()
        # set the values to the all_properties wrappers
        for v in assigned_values:
            if all_properties[v.property_id]['assigned']:
                all_properties[v.property_id]['value'] = v

        if request.method == "POST" and not item.is_variant():
            # form data consist of:
            # - existing properties and values (to update/remove)
            # - added properties and values
            remove_props = _get_selected_ids(request, "remove")
            add_props = _get_selected_ids(request, "add")
            # which properties to save values for
            save_properties = []
            for p_id, p in all_properties.items():
                if p['assigned']:
                    if p_id in remove_props:
                        p['assigned'] = False
                        ProductPropertyRelation.objects.delete(product=owner, property=p_id)
                else:
                    if p_id in add_props:
                        p['assigned'] = True
                        # create new properties_relation entry
                        save_properties.append(p)
            if save_properties:
                try:
                    # determine next position for property in the relationship
                    next_pos = int(owner.properties_relation.aggregate(Max('position')).values()[0]) + 10
                except:
                    next_pos = 0

                for p in save_properties:
                    prop = p['property']
                    ProductPropertyRelation.objects.create(product=item,
                                                           property=prop,
                                                           position=next_pos)
                    next_pos += 10

                self.add_message(request, self.MSG_UPDATED)
                return self.redirect('properties', request, item.id)

        all_properties_values = all_properties.values()
        for p in all_properties_values:
            # for assigned values, print form controls as disabled
            # TODO multivalue
            #if 'form' not in p:
            if p['assigned']:
                prop = p['property']
                form_class = property_value_form_factory(prop)
                try:
                    val = p['value'].get_value()
                except:
                    val = None
                p['form'] = form_class(initial={'value': val}, prefix="f%d" % prop.id)

        context = {
            'item': item,
            'current_properties': [p for p in all_properties_values if p['assigned']],
            'all_properties': [p for p in all_properties_values if not p['assigned']],
        }
        return self.render_tab( 'properties', request, context )

    def XXX__properties_view(self, request, item_id):
        """
        List of properties assigned to a product
        """
        item = self.get_object(item_id)
        if not item.is_variant():
            # get list of all property objects wrapped with some attributes
            all_properties = dict((p.id, {'property': p, 'assigned': False})
                              for p in Property.objects.all())

            # get the IDs of assigned properties and mark them in all_properties
            for p_id in item.properties.values_list('id', flat=True):
                all_properties[p_id]['assigned'] = True
        else:
            # variants inherit their parents' properties
            #   which can not be unassigned nor added nor reordered
            all_properties = dict((p.id, {'property': p, 'assigned': True})
                              for p in item.parent.properties.all())

        # property values are defined on the product variant
        assigned_values = item.property_values.select_related('value_option').all()
        # set the values to the all_properties wrappers
        for v in assigned_values:
            if all_properties[v.property_id]['assigned']:
                all_properties[v.property_id]['value'] = v

        if request.method == "POST":
            # form data consist of:
            # - existing properties and values (to update/remove)
            # - added properties and values
            remove_props = _get_selected_ids(request, "remove")
            add_props = _get_selected_ids(request, "add")
            # which properties to save values for
            save_properties = []
            save_values = []
            for p_id, p in all_properties.items():
                if p['assigned']:
                    if p_id in remove_props:
                        p['assigned'] = False
                        ProductPropertyRelation.objects.delete(product=owner, property=p_id)
                    else:
                        # save new value
                        save_values.append(p)
                else:
                    if p_id in add_props:
                        p['assigned'] = True
                        # create new properties_relation entry
                        save_properties.append(p)
                        # save new value
                        save_values.append(p)
            if save_properties:
                try:
                    # determine next position for property in the relationship
                    next_pos = int(owner.properties_relation.aggregate(Max('position')).values()[0])
                except:
                    next_pos = 0
                for p in save_properties:
                    prop = p['property']
                    ProductPropertyRelation.objects.create(product=item,
                                                           property=prop,
                                                           position=next_pos)

            if save_values:
                # save values for properties
                errors = False
                for p in save_values:
                    prop = p['property']
                    form_class = property_value_form_factory(prop)
                    form = form_class(data=request.POST, prefix="f%d" % prop.id)
                    if form.is_valid():
                        val = p.get('value')
                        if val is None:
                            val = ProductPropertyValue(product=item, property=prop)
                            #p['value'] = val
                        val.set_value(form.cleaned_data['value'])
                        val.save()
                    else:
                        errors = True
                        p['form'] = form
            if not errors:
                self.add_message(request, self.MSG_UPDATED)
                return self.redirect('properties', request, item.id)

        all_properties_values = all_properties.values()
        for p in all_properties_values:
            if 'form' not in p:
                prop = p['property']
                form_class = property_value_form_factory(prop)
                try:
                    val = p['value'].get_value()
                except:
                    val = None
                p['form'] = form_class(initial={'value': val}, prefix="f%d" % prop.id)

        context = {
            'item': item,
            'current_properties': [p for p in all_properties_values if p['assigned']],
            'all_properties': [p for p in all_properties_values if not p['assigned']],
        }
        return self.render_tab( 'properties', request, context )


    def set_property_value_view(self, request, item_id):
        """
        Set a value for a property assigned to a product
        """
        item = self.get_object(item_id)
        parent = item.parent_cached if item.is_variant() else item
        try:
            prop = parent.properties.get(id=request.GET['property'])
        except:
            raise BadParameterException(param='property')

        form_class = property_value_form_factory(prop)
        if request.method == "POST":
            form = form_class(data=request.POST)
            if form.is_valid():
                value = form.cleaned_data['value']
                # TODO multivalue: get -> filter
                try:
                    val = item.property_values.get(property=prop)
                except ProductPropertyValue.DoesNotExist:
                    val = ProductPropertyValue(product=item,
                                                property=prop,
                                                position=10)
                val.set_value(value)
                val.save()

                self.add_message(request, self.MSG_UPDATED)
                return self.redirect('properties', request, item.id)

        else:
            try:
                # TODO multivalue: get -> filter
                val = item.property_values.get(property=prop)
            except:
                form = form_class()
            else:
                form = form_class(initial={'value': val.get_value()})
        context = {
            'item': item,
            'property': prop,
            'form': form,
        }
        return self.render( 'set_property_value', request, context )


    def variants_view(self, request, item_id):
        """
        List of variants assigned to a product
        """
        item = self.get_object(item_id)
        prod = item
        if item.parent_id:
            prod = item.parent
        variants = [prod]
        variants.extend(prod.variants.all())

        context = {
            'item': item,
            'variants': variants,
            'form': ProductVariantAddForm(),
        }
        return self.render_tab( 'variants', request, context )


    def categories_view(self, request, item_id):
        """
        List of categories assigned to a product
        """
        item = self.get_object(item_id)
        categories_override = True
        if item.is_variant() and not item.variant_cached.own_categories:
            # using parent's categories
            categories = item.parent.categories
            categories_override = False
        else:
            categories = item.categories

        selected_categories = [cat.id for cat in categories.all()]
        if request.method == "POST":
            if item.is_variant():
                # check presence of categories_override argument
                categories_override = request.POST.get("categories_override")
                item.categories_override = bool(categories_override)
                item.save()
                if categories_override:
                    # ensure we don't occasionally update parent's categories
                    categories = item.categories

            if categories_override:
                cats = _get_selected_ids(request, "categories")
                new_cats = []
                old_cats = []
                remove_cats = []

                for cat_id in cats:
                    if cat_id in selected_categories:
                        old_cats.append(cat_id)
                    else:
                        new_cats.append(cat_id)
                for cat_id in selected_categories:
                    if cat_id not in old_cats:
                        remove_cats.append(cat_id)

                try:
                    categories.remove(*remove_cats)
                    categories.add(*new_cats)
                except Category.DoesNotExist:
                    self.add_message(request, self.MSG_ERROR)
                else:
                    # update list
                    selected_categories = [cat.id for cat in categories.all()]
                    self.add_message(request, self.MSG_UPDATED)

        if item.is_variant:
            override_form = ProductVariantCategoriesOverrideForm(instance=item)
        else:
            override_form = None
        context = {
            'item': item,
            'form': override_form,
            'categories': Category.objects.as_tree(),
            'categories_override': categories_override,
            'selected_categories': selected_categories,
        }
        return self.render_tab( 'categories', request, context )


    def add_variant_view(self, request, item_id):
        """
        Add a variant to a product
        """
        item = self.get_object(item_id)
        if item.is_variant():
            item = item.parent
        if request.method == "POST":
            form = ProductVariantAddForm(data=request.POST)
            if form.is_valid():
                input = form.cleaned_data
                variant = item.create_variant(
                    sku=input['sku'],
                    variant_name=input['variant_name'],
                    )
                variant.save()
                self.add_message(request, self.MSG_ADDED)
                return self.redirect('data', request, variant.id)
        else:
            form = ProductVariantAddForm()

        context = {
            'item': item,
            'form': form,
        }
        return self.render( 'add_variant', request, context )


    def search_view(self, request):
        """
        Find a product by name
        """
        term = request.GET.get("term")
        if term is None or term == "":
            found_items = None
        else:
            #term = term.strip()
            #found_items = Product.objects.filter(name__istartswith=term)
            found_items = Product.objects.search(term)
        context = {
            "term": term,
            "found_items": found_items,
        }
        return self.render( 'search', request, context )



    def copy_view(self, request, item_id):
        """
        Create a copy of the item
        """
        item = self.get_object(item_id)

        form_class = getattr(self, 'copy_form_class', self.add_form_class or self.form_class)
        if request.method == "POST":
            form = form_class(data=request.POST)
            if form.is_valid():
                try:
                    new_item = item.copy(**form.cleaned_data)
                except IntegrityError:
                    self.add_message(request, self.MSG_ERROR_UNIQUE)
                else:
                    self.add_message(request, self.MSG_ADDED)
                    return self.redirect('edit', request, new_item.id)
        else:
            form = form_class(instance=item)
        context = {
            'item': item,
            'form': form,
            }
        return self.render( 'copy', request, context )



    #def dimensions_view(self, request, item_id):
        #return self._form_tab_view(request, item_id, 'dimensions')

    def x_properties_view(self, request, item_id):
        """
        Display a list of properties and their values
        """
        item = self.get_object(item_id)
        proplist = item.product.properties.all()
        propdict = dict([ (p.id, []) for p in proplist ])
        variant_props = item.property_values.all()
        for pv in variant_props:
            try:
                propdict[pv.property_id].append(pv)
            except KeyError:
                # ??? delete property value
                pass
        product_properties = [(p, propdict[p.id]) for p in proplist]
        # ### old ###
        #product_properties = [(p, item.get_property_value(p)) for p in item.product.properties.all()]
        context = {
            'item': item,
            'product_properties': product_properties,
            }
        return self.render_tab( 'properties', request, context )


    def change_property_view(self, request, item_id):
        """
        Change property values
        """
        item = self.get_object(item_id)
        try:
            prop_id = request.GET['property']
        except KeyError:
            raise BadParameterException('property')

        # ensure the base product has the property assigned
        try:
            prop = item.product.properties.get(id=prop_id)
        except Property.DoesNotExist:
            raise BadParameterException('property')

        # different algorithms of handling single- and multivalue properties
        if prop.is_multivalue:
            values = list(item.property_values.filter(property_id=prop_id))
            # create an empty value to handle adding values to multivalue properties
            values.append(ProductPropertyValue(property=prop, product=item))
        else:
            try:
                propval = item.property_values.get(property_id=prop_id)
            except ProductPropertyValue.DoesNotExist:
                propval = ProductPropertyValue(property=prop, product=item)
            values = [propval, ]

        formclass = property_value_form_factory(prop)
        form = None
        forms = []
        if request.method == "POST":
            #form = PropertyValueForm(instance=propval, data=request.POST)
            error = False
            for i, propval in enumerate(values):
                form = formclass(data=request.POST, prefix="f%d" % i)
                forms.append(form)
                if form.is_valid():
                    #form.save()
                    val = form.cleaned_data['value']
                    if val is None:
                        # for a multivalue property, given an empty value
                        # the existing property_value is to be deleted
                        # for a new (blank, extra) form, the empty value is ignored
                        if propval.id:
                            propval.delete()
                    else:
                        propval.set_value(val)
                        propval.save()
                else:
                    error = True
            if not error:
                self.add_message(request, self.MSG_UPDATED)
                return self.redirect('properties', request, item.id)
            else:
                self.add_message(request, self.MSG_ERROR)

        else:
            #form = PropertyValueForm(instance=propval)
            for i, propval in enumerate(values):
                form = formclass(initial={'value': propval.get_value()},
                        prefix="f%d" % i)
                forms.append(form)
            # NOTE: not needed, because an empty ProductPropertyValue is always added to list
            # add an empty form to be able to add a value to a multivalue property
            #if prop.is_multivalue:
                #form = formclass(prefix="f%d" % (i+1))
                #forms.append(form)

        context = {
            'item': item,
            'property': propval.property,
            'form': form,
            'forms': forms,
            #'form_field': form.get_value_field(),
            }
        return self.render( 'change_property', request, context )


    def stock_view(self, request, item_id):
        """
        Manage variant's sale attributes
        """
        item = self.get_object(item_id)
        context = {
            'item': item,
            }
        return self.render_tab( 'stock', request, context )


    def sale_view(self, request, item_id):
        """
        Manage variant's sale attributes
        """
        return self._form_tab_view(request, item_id, 'sale')


    def init_tabs(self):
        super(ProductDispatcher, self).init_tabs()
        #if not settings.VARIANTS_ENABLED:
            #self.tabs_by_name['variants']['disabled'] = True
        if settings.PRODUCTS_ADMIN_TABS_DISABLED:
            for tab_name in settings.PRODUCTS_ADMIN_TABS_DISABLED:
                self.tabs_by_name[tab_name]['disabled'] = True



class PropertyDispatcher(TabsDispatcher, PageDispatcherMixin):
    """
    The Property model-specific dispatcher
    """
    add_form_class = PropertyDataForm
    model = Property
    tabs_descriptor = (
        ('data', _('Data'), PropertyDataForm),
        ('values', _('Values'), None),
        ('products', _('Products'), None),
    )


    #def data_view(self, request, item_id):
        #return self._form_tab_view(request, item_id, 'data')


    def values_view(self, request, item_id):
        """
        Show a list of property values
        NOTE: if the property is of option type, show the options and
            controls to add/remove them;
            otherwise, show just all the existing values
        """
        item = self.get_object(item_id)

        if item.value_type == Property.VALUE_TYPE_OPTION:
            values = item.options.all() # pass PropertyOption objects, to make use of their IDs
            is_editable = True
        else:
            attr = 'value_%s' % item.value_type
            values = item.property_values.values_list(attr, flat=True).distinct()
            #values = item.property_values.all()
            is_editable = False
        context = {
            'item': item,
            'values': values,
            'is_editable': is_editable,
            }
        return self.render_tab( 'values', request, context )


    def add_option_view(self, request, item_id):
        """
        """
        item = self.get_object(item_id)
        if request.method == "POST":
            form = PropertyOptionForm(data=request.POST)
            if form.is_valid():
                opt = item.options.create(**form.cleaned_data)
                return self.redirect('values', request, item.id)
            else:
                self.add_message(request, self.MSG_ERROR)
        else:
            form = PropertyOptionForm()
        context = {
            'item': item,
            'form': form,
            }
        return self.render( 'add_option', request, context )


    def products_view(self, request, item_id):
        """
        Show a list of products which have the property
        """
        item = self.get_object(item_id)
        context = {
            'item': item,
            }
        return self.render( 'values', request, context )


def setup(dispatcher):
    dispatcher.register(CategoryDispatcher(Category), menuitem='catalog')
    dispatcher.register(ProductDispatcher(Product), menuitem='catalog')
    dispatcher.register(PageDispatcher(Manufacturer), menuitem='catalog')
    dispatcher.register(PropertyDispatcher(Property), menuitem='catalog')
