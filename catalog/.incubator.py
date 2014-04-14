
# ### was in yz.catalog.utils ###
def filter_variants(product, filter_values):
    """
    """
    context = {}
    filters = {}
    selected_variants = product.get_active_variants()
    context['product_variants'] = selected_variants
    props = product.get_properties()
    for prop in props:
        try:
            filter_var = filter_values[prop.slug]
        except KeyError:
            pass
        else:
            logger.debug("filter_var[%s]=%s", prop.slug, filter_var)
            try:
                filters[prop.id] = prop.value_from_string(filter_var)
            except ValueError:
                pass
    if filters:
        selected_variants = product.get_all_variants_properties(current_values=filters)
        #if not selected_variants:
            #raise http.Http404
            #selected_variants = product.get_all_variants_properties()
        context['selected_variants'] = selected_variants
        context['selected_properties'] = filters

    # select the default variant
    if selected_variants:
        current_variant = selected_variants[0]
    else:
        current_variant = product.get_default_variant()
    context['current_variant'] = current_variant
    return context

# ### was Product methods ###
    def get_all_variants_properties(self, active=True, current_values={}):
        """
        Get the mapping of property values for a product and its variants (from cache)
        which match a given condition of (property=value)* combinations.
        current_values: key is a property id, value is the property value
        The output mapping's format is { variant_id: { property_id: [values] }}
        """
        prod = self.parent_cached if self.is_variant() else self
        all_variants = ProductPropertyValue.objects.get_all_variants_properties(prod, active=active)
        for prop_id, val in current_values.items():
            # make up a new mapping of variants matching the conditions
            all_variants = {variant_id: variant_data
                            for variant_id, variant_data in all_variants.items()
                            if val in variant_data.get(prop_id, ())}
        return all_variants

    def get_available_values(self, property, current_values={}):
        """
        Get a list of available property values for the product and its variants
        """
        all_values = self.get_all_variants_properties(active=True, current_values=current_values)
        # join all value lists into one
        available = reduce(lambda res_list, val_list: res_list + val_list,
                        [variant_data.get(property.id, []) for variant_data in all_values.values()])
        return sorted(set(available))

