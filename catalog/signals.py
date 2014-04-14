from django.dispatch import Signal

# sender is a product; kwargs are request and context
product_viewed = Signal()
