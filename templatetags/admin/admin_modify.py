from django.contrib.admin.templatetags.admin_modify import *


def custom_submit_row(context):
    """
    Display the row of buttons for delete and save.
    """
    show_delete_link = context.get('show_delete_link')
    show_save_as_new = context.get('show_save_as_new')
    show_save_and_add_another = context.get('show_save_and_add_another')
    show_save_and_continue = context.get('show_save_and_continue')
    show_save = context.get('show_save')

    context = submit_row(context)

    show_delete_link = (
        show_delete_link if show_delete_link is not None else context['show_delete_link']
    )
    show_save_as_new = (
        show_save_as_new if show_save_as_new is not None else context['show_save_as_new']
    )
    show_save_and_add_another = (
        show_save_and_add_another
        if show_save_and_add_another is not None
        else context['show_save_and_add_another']
    )
    show_save_and_continue = (
        show_save_and_continue
        if show_save_and_continue is not None
        else context['show_save_and_continue']
    )
    show_save = show_save if show_save is not None else context['show_save']

    context.update(
        dict(
            show_delete_link=show_delete_link,
            show_save_as_new=show_save_as_new,
            show_save_and_add_another=show_save_and_add_another,
            show_save_and_continue=show_save_and_continue,
            show_save=show_save,
        )
    )
    return context


@register.tag(name='submit_row')
def submit_row_tag(parser, token):
    return InclusionAdminNode(
        parser, token, func=custom_submit_row, template_name='submit_line.html'
    )
