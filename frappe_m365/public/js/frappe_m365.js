frappe.provide("frappe");

frappe.realtime.on("m365_groups", function (output) {
    frappe.show_alert(output, 15);
});