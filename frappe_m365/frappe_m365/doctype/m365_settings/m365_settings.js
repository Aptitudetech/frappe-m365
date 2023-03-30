// Copyright (c) 2023, aptitudetech and contributors
// For license information, please see license.txt

frappe.ui.form.on('M365 Settings', {
	refresh: (frm) => {
		if(!frm.doc.graph_api){
			frm.set_value('m365_graph_url', 'https://graph.microsoft.com/v1.0');
		}

		frm.fields_dict['module_settings'].grid.get_field('role').get_query = function(doc, cdt, cdn) {
			let roles = [];
			$.each(cur_frm.doc.module_settings, function(index, row){
				roles.push(row.role);
			});

			return {
				filters:[
					['Role', 'name', 'not in', roles]
				]
			}
		}
	}
});

frappe.ui.form.on("M365 Groups Module Settings", {
	update_user: function(frm, cdt, cdn){
		let child = locals[cdt][cdn];
		if(child.__islocal == 1){
			frappe.msgprint("Please save the form first.");
		}else if(child.role){
			frappe.call({
				"method": "frappe_m365.frappe_m365.doctype.m365_settings.m365_settings.update_group_members",
				"args": {"role": child.role, "group": child.default_group},
				"freeze": 1,
				"freeze_message": "<h4>Please wait while we are updating members in office 365 group...</h4>"
			})
		}else{
			frappe.msgprint("Please select a Role.");
		}
	}
});
