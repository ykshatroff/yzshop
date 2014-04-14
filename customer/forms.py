import re
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

from yz.core.models import Shop

from .models import Customer
from .models import CustomerAddress
from .models import Address


class PhoneForm(forms.Form):
    """
    Use prefix kwarg to distinguish one phone field from another
    """
    country_code = forms.IntegerField(label=_(u'country code'),
            required=False)
    region_code = forms.IntegerField(label=_(u'region code'),
            required=False)
    number = forms.CharField(label=_(u'phone number'), max_length=10,
            validators=[RegexValidator(regex=r'^[\d\s-]*$',
                        message=_(u'Please enter the phone number up to 10 digits'))],
            required=False)

    def clean(self):
        """
        Check that either all fields are blank or at least country_code and number are filled
        """
        data = super(PhoneForm, self).clean()
        return data

    @classmethod
    def from_string(cls, value):
        """
        Get a dict of field values from a phone string
        """
        try:
            result = value.split(" ", 2) # not more than 3 values
        except:
            result = ('', '', '')
        else:
            if len(result) < 3:
                # we don't know which values are filled if less than all
                # assume the last one is the phone number, ignore the other if there are two
                result = ('', '', result.pop())
        fields = ('country_code', 'region_code', 'number')
        return dict(zip(fields, result))

#class PhoneFormField(forms.Field):
    #def __init__(self, **kwargs):
        #super(PhoneComboField, self).__init__(widget=PhoneFormWidget, **kwargs)



class PhoneComboWidget(forms.MultiWidget):
    def __init__(self, **kwargs):
        """
        """
        kwargs['widgets'] = (
            forms.TextInput, forms.TextInput, forms.TextInput
        )
        super(PhoneComboWidget, self).__init__(**kwargs)

    def decompress(self, value):
        """
        Make a list of 3 phone components from a string value
        Takes a string separated by spaces
        """
        if value == "" or value is None:
            result = ('', '', '')
        else:
            result = value.split(" ")
        return result


class PhoneComboField(forms.MultiValueField):
    """
    """
    def __init__(self, **kwargs):
        """
        """
        # remove 'required' from kwargs so that the compress() handles it
        # otherwise Django's logic would not allow correct checking
        self.real_required = kwargs.pop("required", True)
        kwargs['required'] = False
        kwargs.setdefault('help_text', _(u"country code / region code / phone number"))

        kwargs['fields'] = (
                forms.IntegerField(label=_(u'country code'), min_value=1,
                ),
                forms.IntegerField(label=_(u'region code'), min_value=1,
                ),
                forms.CharField(label=_(u'phone number'), max_length=10,
                        validators=[RegexValidator(regex=r'^[\d\s-]*$',
                                message=_(u'up to 10 digits'))],
                ),
        )
        kwargs['widget'] = PhoneComboWidget
        super(PhoneComboField, self).__init__(**kwargs)

    def compress(self, values):
        """
        Check that either all fields (except maybe region code), or none, are filled
        """
        if len(values) != 3:
            raise ValidationError(_(u"Invalid count of values for a phone"))
        result = []
        is_blank = True # flag
        for val in values:
            if val is None:
                # do not change is_blank
                val = ""
            elif val != "":
                is_blank = False
                val = re.sub(r'\D', '', "%s" % val)
                if val == "":
                    raise ValidationError(_(u"Invalid value for a phone"))
            result.append(val)
        if is_blank and self.real_required:
            raise ValidationError(_(u"Required field"))
        if result[2] == "" and not is_blank:
            raise ValidationError(_(u"Empty phone number"))
        return " ".join(result)



class PhoneField(forms.CharField):
    """
    """

    def validate(self, value):
        if value:
            try:
                phone = str(value).strip()
            except:
                raise ValidationError(_(u'Invalid phone number'))
            if not re.match(r'^\+?[\d()\s-]+$', phone):
                raise ValidationError(_(u'Invalid phone number'))

    def clean(self, value):
        value = super(PhoneField, self).clean(value)
        if value == "":
            # OK to have no phone number supplied
            if not self.required:
                return ""
            raise ValidationError(self.default_error_messages['required'])
        # remove all non-digits
        value = re.sub(r'\D', '', value)
        # allow to check unique etc
        return value


class AuthenticationForm(forms.Form):
    """
    Login form for customers
    """
    username = forms.CharField(required=False, label=_(u'e-mail'))
    phone = PhoneField(required=False, label=_(u'phone'))
    password = forms.CharField(required=True, label=_(u'password'), widget=forms.PasswordInput)

    def clean(self):
        """
        return either a username(e-mail) or phone, but not both
        """
        # TODO see below
        data = super(AuthenticationForm, self).clean()
        username = data.get('username')
        phone = data.get('phone')
        if not (username or phone):
            raise ValidationError, _(u"One of fields username or phone is required")
        if not username:
            data['username'] = phone

        return data

    def authenticate(self):
        if self.is_valid():
            username = self.cleaned_data['username']
            password = self.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if not user:
                self._errors['__all__'] = self.error_class([_(u"Invalid username or password")])
            return user
        return None


class RegisterForm(forms.Form):
    """
    Account registration form
    """
    name = forms.CharField(label=_(u'your full name'), help_text=_('Example: John Fitzgerald Smith'),
            max_length=200)
    company_name = forms.CharField(label=_(u'your company name'), help_text=_('Example: Bananaland LLC'),
            required=False, max_length=200)
    email = forms.EmailField(label=_(u"e-mail"), max_length=50)
    phone = PhoneField(label=_(u'phone'), help_text=_('Example: +44 012345678'))
    password_1 = forms.CharField(
        label=_(u"password"), widget=forms.PasswordInput(), max_length=20)
    password_2 = forms.CharField(
        label=_(u"confirm password"), widget=forms.PasswordInput(), max_length=20)

    def clean_password_2(self):
        """Validates that password 1 and password 2 are the same.
        """
        p1 = self.cleaned_data.get('password_1')
        p2 = self.cleaned_data.get('password_2')

        if not (p1 and p1 == p2):
            raise forms.ValidationError(_(u"The two passwords do not match."))

        return p2

    def clean(self):
        """
        """
        data = super(RegisterForm, self).clean()
        return data


class AddressForm(forms.ModelForm):
    """
    This form must suit for CustomerAddress as well as OrderAddress
        which both share the same Address base class
    NOTE: this form shares field names with the CustomerForm defined below:
        'name', 'company_name', 'email', 'phone'
    """
    #use_customer_name = forms.BooleanField(label=_(u'name is the same'), default=True)
    #use_customer_email = forms.BooleanField(label=_(u'email is the same'), default=True)
    #use_customer_phone = forms.BooleanField(label=_(u'phone is the same'), default=True)

    country = forms.ModelChoiceField(label=_(u'country'),
            queryset=Shop.get_default_shop().shipping_countries.all())
    phone = PhoneComboField(label=_(u'phone'))

    class Meta:
        model = Address

    def __init__(self, address_required=False, *args, **kwargs):
        """
        add address_required parameter
        """
        self.address_required = address_required
        initial = kwargs.setdefault("initial", {})
        initial['country'] = Shop.get_default_shop().get_default_country()
        super(AddressForm, self).__init__(*args, **kwargs)
        for fn in ('address', 'town', 'country', 'zip_code'):
            self.fields[fn].required = address_required

    #def clean_address(self):
        #value = self.cleaned_data['address']
        #if self.address_required and "" == value:
            #raise ValidationError()

class CustomerForm(forms.ModelForm):
    """
    Customer identity form
    NOTE: this form shares field names with the AddressForm defined above
    The form is less forgiving about blank data than the Customer model
    """

    name = forms.CharField(label=_(u'your full name'), help_text=_('Example: John Fitzgerald Smith'),
            max_length=200)
    company_name = forms.CharField(label=_(u'your company name'), help_text=_('Example: Bananaland LLC'),
            required=False, max_length=200)
    email = forms.EmailField(label=_(u"e-mail"), max_length=50)
    phone = PhoneComboField(label=_(u'phone'))
    class Meta:
        model = Customer
        fields = ('name', 'company_name', 'email', 'phone')


