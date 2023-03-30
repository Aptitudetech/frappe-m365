# Copyright (c) 2023, aptitudetech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class M365Settings(Document):
	pass

@frappe.whitelist()
def update_group_members(role, group):
	try:
		users = frappe.db.get_list(
			"Has Role",
			{
				"parenttype": "User", "role": role,
				"parent": ["not in", ["Administrator", "Guest"]]
			},
			"parent", ignore_permissions=1
		)

		group_doc = frappe.get_doc("M365 Groups", group)
		m365_group_members = [user.user for user in group_doc.m365_groups_member]
		for user in users:
			if user.parent not in m365_group_members:
				group_doc.append("m365_groups_member", {"user": user.parent})
	
		group_doc.save()
		group_doc.update_m365_groups_members()
	except Exception as e:
		frappe.msgprint(e)