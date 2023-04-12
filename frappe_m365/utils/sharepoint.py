import frappe
from frappe import _, enqueue
from frappe_m365.utils import get_request_header, make_request
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification

import os

'''
	mapping with sharepoint
'''

M365 = "M365 Settings"
ContentType = {"Content-Type": "application/json"}


def trigger_sharepoint(request, group, doctype=None, docname=None, filepath=None, filedoc=None):
    sharepoint = SharePoint(
        group=group, doctype=doctype,
        docname=docname, filepath=filepath, filedoc=filedoc
    )
    
    if (request == "MAP"):
        sharepoint.run_sharepoint_mapping()
    elif (request == "UPLOAD"):
        sharepoint.run_sahrepoint_upload()


class SharePoint(object):
    def __init__(self, **kwargs):
        self.user = frappe.session.user
        self.group_doc = kwargs.get("group")
        self.group_id = self.group_doc.m365_group_id
        self.doctype = kwargs.get("doctype")
        self.docname = kwargs.get("docname")
        self.filepath = kwargs.get("filepath")
        self.filedoc = kwargs.get("filedoc")
        self.sharepoint_list_id = self.group_doc.m365_sharepoint_id
        self.settings = frappe.get_single(M365)
        self.group_url = f'{self.settings.m365_graph_url}/groups/{self.group_id}/'

    def run_sharepoint_mapping(self):
        self.mapping_modules_in_shareopint()
        self.mapping_modules_doctype_in_sharepoint()
        msg = "M365 Group(<b>" + self.group_doc.name + "</b>) has been created and mapped sucessfully."
        self.send_notification_to_user(msg)

    def send_notification_to_user(self, msg):
        notification_doc = {
            "type": "Alert",
            "document_type": self.group_doc.doctype,
            "document_name": self.group_doc.name,
            "subject": msg,
            "email_content": None
        }
        doc = frappe._dict(notification_doc)
        notification = frappe.new_doc("Notification Log")
        notification.update(doc)
        notification.for_user = self.user
        notification.insert(ignore_permissions=True)
        frappe.publish_realtime(event='m365_groups', message=msg, user=self.user)

    def get_sharepoint_list_items(self, list_id):
        '''
            fetching sharepoint sublist based on 
            list id information
        '''
        self.sharepoint_list_items = []
        headers = get_request_header(self.settings)
        headers.update(ContentType)
        url = f'{self.group_url}drive/items/{list_id}/children'

        response = make_request('GET', url, headers, None)
        if response.status_code == 200 or response.ok:
            for items in response.json()['value']:
                self.sharepoint_list_items.append({"name": items["name"], "id": items["id"]})
        else:
            frappe.log_error("sharepoint list items fetch error", response.text)

        return self.sharepoint_list_items

    def mapping_modules_in_shareopint(self):
        self.modules = frappe.db.get_list("Module Def", ["name"])
        self.modules_in_sharepoint = self.get_sharepoint_list_items(self.sharepoint_list_id)
        self.existed_modules = [item['name'] for item in self.modules_in_sharepoint]

        for module in self.modules:
            if module.name not in self.existed_modules:
                self.create_sharepoint_list_item(self.sharepoint_list_id, module.name)

    def create_sharepoint_list_item(self, list_id, list_item):
        headers = get_request_header(self.settings)
        headers.update(ContentType)
        url = f'{self.group_url}drive/items/{list_id}/children'
        body = {
            "name": f'{list_item}',
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }

        response = make_request('POST', url, headers, body)
        if not response.ok:
            frappe.log_error("sharepoint list item creation error", response.text)
            return None
        else:
            return response.json()["id"]
        
    def mapping_modules_doctype_in_sharepoint(self):
        self.modules = self.get_sharepoint_list_items(self.sharepoint_list_id)
        for module in self.modules:
            self.doctype_in_sharepoint = self.get_sharepoint_list_items(module["id"])
            self.sharepoint_doctypes = [doc["name"] for doc in self.doctype_in_sharepoint]
            self.doctypes = frappe.db.get_list("DocType", {"module": module["name"], "istable": 0}, "name")

            for doc in self.doctypes:
                if doc['name'] not in self.sharepoint_doctypes:
                    self.create_sharepoint_list_item(module["id"], doc['name'])

    def run_sahrepoint_upload(self):
        data_id = None
        doctype_id = None
        module_id = None

        # fetching sharepoint root id
        doctype_module = frappe.db.get_value("DocType", {"name": self.doctype}, "module")
        module_id = self.get_data_id_from_sharepoint(self.sharepoint_list_id, doctype_module)

        if module_id:
            doctype_id = self.get_data_id_from_sharepoint(module_id, self.doctype)
        else:
            module_id = self.create_sharepoint_list_item(self.sharepoint_list_id, doctype_module)
            doctype_id = self.get_data_id_from_sharepoint(module_id, self.doctype)

        if module_id and not doctype_id:
            doctype_id = self.create_sharepoint_list_item(module_id, self.doctype)
            data_id = self.get_data_id_from_sharepoint(doctype_id, self.docname)
        else:
            data_id = self.get_data_id_from_sharepoint(doctype_id, self.docname)

        if module_id and doctype_id and not data_id:
            data_id = self.create_sharepoint_list_item(doctype_id, self.docname)

        file_content = self.get_file_content()
        file_name = self.filepath.split("/")[-1]

        if data_id and file_content and file_name:
            headers = get_request_header(self.settings)
            headers.update({"Content-Type": "text/plain"})
            url = f'{self.group_url}drive/items/{data_id}:/{file_name}:/content'

            response = make_request('PUT', url, headers, file_content)
            if not response.ok:
                frappe.log_error("File Upload Error", response.text)
            elif response.ok:
                frappe.db.set_value("File", self.filedoc, "uploaded_to_sharepoint", 1)
                if self.settings.replace_file_link:
                    frappe.db.set_value("File", self.filedoc,"file_url", response.json()['webUrl'])
                    self.remove_file() 


    def get_data_id_from_sharepoint(self, list_id, list_item):
        _id = None
        list_items = self.get_sharepoint_list_items(list_id)
        for item in list_items:
            if (list_item == item['name']):
                _id = item['id']
        return _id
    
    def get_file_content(self):
        try:
            return open(self.filepath, 'rb')
        except Exception as e:
            frappe.log_error('file read error', e)
            return None

    def remove_file(self):
        try:
            os.remove(self.filepath)
        except Exception as e:
            frappe.log_error("File remove error", e)
