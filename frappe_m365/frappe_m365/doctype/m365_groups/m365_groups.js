// Copyright (c) 2023, aptitudetech and contributors
// For license information, please see license.txt

frappe.ui.form.on('M365 Groups', {
	refresh: function(frm) {
		frm.trigger('set_default_values');
		if (frm.doc.enable && !frm.doc.__islocal) {
			if(!frm.doc.m365_group_id){
				frm.trigger('add_connect_button');
			}else{
				frm.trigger('update_group_members');
			}
		}
	},

	set_default_values: function (frm) {
		if (!frm.doc.m365_group_description) {
			frm.set_value('m365_group_description', 'This group has been created from Frappe-M365');
		}

		if (frm.doc.group_id) {
			frm.toggle_enable("mailnickname", 1);
		}
	},

	m365_group_name: function (frm) {
		let parts = frm.doc.m365_group_name.split(" ");
		let abbr = $.map(parts, function (p) {
			return p ? p.substr(0, 1) : null;
		}).join("");
		frm.set_value("mailnickname", abbr.toLowerCase());
	},

	add_connect_button: function (frm) {
		frm.add_custom_button(__("Connect to M365 Groups"), function () {
			if (!frm.is_dirty()) {
				frappe.call({
					method: "run_m365_groups_flow",
					freeze: 1,
					freeze_message: "<h4>Please wait while we are connecting and mapping with M365 groups...</h4>",
					doc: frm.doc,
					callback: function (r) {
						frm.reload_doc();
					}
				});
			} else {
				frappe.msgprint("Please save the form first.")
			}
		});
	},

	update_group_members: function (frm) {
		frm.add_custom_button(__("Update M365 Group Member(s)"), function () {
			if (frm.is_dirty()) {
				frappe.msgprint("Please save the form first.")
			} else {
				frappe.call({
					method: "update_m365_groups_members",
					freeze: 1,
					freeze_message: "<h4>Please wait while we are updating members in M365 Group...</h4>",
					doc: frm.doc,
					callback: function (r) {
						frm.reload_doc();
					}
				});
			}
		});
	}
});
