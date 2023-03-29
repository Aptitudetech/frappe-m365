// Copyright (c) 2023, aptitudetech and contributors
// For license information, please see license.txt

frappe.ui.form.on('M365 Settings', {
	refresh: (frm) => {
		if(!frm.doc.graph_api){
			frm.set_value('m365_graph_url', 'https://graph.microsoft.com/v1.0');
		}
	}
});
