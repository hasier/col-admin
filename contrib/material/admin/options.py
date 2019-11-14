from django.contrib.admin.options import InlineModelAdmin
from material.admin.options import *


class MaterialInlineModelAdmin(InlineModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.formfield_overrides.update(FORMFIELD_FOR_DBFIELD_MATERIAL)

    @property
    def media(self):
        extra = '' if settings.DEBUG else '.min'
        js = [
            'vendor/jquery/jquery%s.js' % extra,
            'jquery.init.js',
            'core.js',
            'actions%s.js' % extra,
            'urlify.js',
            'prepopulate%s.js' % extra,
            'vendor/xregexp/xregexp%s.js' % extra,
        ]
        material_js = [
            'material/admin/js/RelatedObjectLookups.min.js',
        ]
        return forms.Media(js=['admin/js/%s' % url for url in js] + material_js)


class MaterialStackedInline(MaterialInlineModelAdmin):
    template = 'admin/edit_inline/stacked.html'


class MaterialTabularInline(MaterialInlineModelAdmin):
    template = 'admin/edit_inline/tabular.html'
