from django.forms import Field

# Add monkey method to help automatically set up actions based on field class
Field.get_class_for_css = lambda self: self.__class__.__name__
