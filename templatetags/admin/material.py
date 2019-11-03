from material.admin.templatetags.material import *


@register.tag(name='additional_submit_row')
def additional_submit_row_tag(parser, token):
    from templatetags.admin.admin_modify import custom_submit_row

    return InclusionAdminNode(
        parser, token, func=custom_submit_row, template_name='additional_submit_line.html'
    )


@register.simple_tag(takes_context=True)
def cookie_current_theme(context, preview):
    return 'red'
