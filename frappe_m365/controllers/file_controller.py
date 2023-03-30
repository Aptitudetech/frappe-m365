import frappe
from frappe import _
import os

M365 = "M365 Settings"
GROUPS = "M365 Groups"


def file_upload(doc, method):
    doctype = doc.attached_to_doctype
    docname = doc.attached_to_name
    group_doc, group_id, filepath = None, None, None

    if (doctype and docname and method == "after_insert" and frappe.db.exists(M365)):
        group_settings = frappe.get_single(M365)
        if group_settings.enable_file_sync:
            group_doc, group_id = get_group_doc(doctype, group_settings)
            filepath = get_file_path(doc)

    if (group_doc and group_id and filepath):
        gp_doc = frappe.get_doc(GROUPS, group_doc)
        frappe.enqueue(
            "frappe_m365.utils.sharepoint.trigger_sharepoint", queue="long",
            request="UPLOAD", group=gp_doc, doctype=doctype, docname=docname,
            filepath=filepath, filedoc=doc.name, timeout=-1
        )


# preparing complete file path
def get_file_path(doc):
    path = "private/files" if doc.is_private else "public/files"
    filepath = os.path.abspath(os.curdir) + "/" + frappe.get_site_path(path, doc.file_name)
    return filepath


# return M365 group doc based on settings in M365 Groups Settings doctype
def get_group_doc(doctype, group_settings):
    role, group, group_id = None, None, None
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    module = frappe.db.get_value("DocType", doctype, "module")

    for entry in group_settings.module_settings:
        if (module == entry.module and user in get_group_members(entry.default_group)):
            role = entry.role
            group = entry.default_group
            group_id = frappe.db.get_value(GROUPS, entry.default_group, "m365_group_id")

    if ((role and group and role in user_roles) or (not role and group)):
        return group, group_id
    elif (user in get_group_members(group_settings.default_m365_group)):
        group_id = frappe.db.get_value(GROUPS, group_settings.default_m365_group, "m365_group_id")
        return group_settings.default_m365_group, group_id
    else:
        return group, group_id


def get_group_members(group):
    users = frappe.db.get_list(
        "M365 Groups Member",
        {"parent": group, "parenttype": 'M365 Groups'},
        "user", ignore_permissions=True
    )
    return [user.user for user in users]
