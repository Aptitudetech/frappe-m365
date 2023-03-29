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
