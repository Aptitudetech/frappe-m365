# Copyright (c) 2023, aptitudetech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe_m365.utils import get_request_header, make_request
import time

M365 = "M365 Settings"
ContentType = {"Content-Type": "application/json"}


class M365Groups(Document):
    @frappe.whitelist()
    def run_m365_groups_flow(self):
        '''
            initiating the flow of M365 group, fetching the
            information of the groups, if exist in M365 then
            saving the info of group
            otherwise start new group creation
        '''
        if frappe.db.exists(M365):
            self._settings = frappe.get_single(M365)
            self.is_m365_group_exist()
        else:
            message = '''
				<p>
					Please update Oauth Settings in
					<a href='/app/m365-settings' style='color: #2490EF'>
						<b>M365 Settings</b>
					</a>
				</p>
			'''
            frappe.msgprint(message)

    def m365_groups_info(self):
        group_info = []
        headers = get_request_header(self._settings)
        url = f'{self._settings.m365_graph_url}/groups'
        groups = make_request('GET', url, headers, None)
        if groups.status_code == 200:
            for group in groups.json()['value']:
                if (group['displayName'] == self.m365_group_name):
                    group_info.append({'name': group['displayName'], 'id': group['id']})
        return group_info

    def get_user_info(self):
        '''
            getting user information which will be used
            for making owner of the group
        '''
        headers = get_request_header(self._settings)
        url = f'{self._settings.m365_graph_url}/me'
        return make_request('GET', url, headers, None).json()['id']

    def is_m365_group_exist(self):
        if not self.m365_group_id:
            group_info = self.m365_groups_info()
            if group_info:
                self.db_set('m365_group_id', group_info[0]['id'])
                self.m365_group_id = group_info[0]['id']
                frappe.msgprint('M365 Group has been successfully mapped.')
                self.initialize_M365_groups_services()
            else:
                self.create_m365_group()
        else:
            self.initialize_M365_groups_services()

    def create_m365_group(self):
        user_id = self.get_user_info()
        url = f'{self._settings.m365_graph_url}/groups'
        headers = get_request_header(self._settings)
        headers.update(ContentType)
        body = {
            "description": f"{self.m365_group_description}",
            "displayName": f"{self.m365_group_name}",
            "groupTypes": ["Unified"],
            "mailEnabled": True,
            "mailNickname": f"{self.mailnickname}",
            "securityEnabled": False,
            "owners@odata.bind": [f"https://graph.microsoft.com/v1.0/users/{user_id}"]
        }

        response = make_request('POST', url, headers, body)
        if (response.status_code == 201):
            self.db_set('m365_group_id', response.json()['id'])
            self.m365_group_id = response.json()['id']
            frappe.msgprint('M365 Group has been created successfully.')
            self.initialize_M365_groups_services()
        else:
            frappe.log_error("M365 Group Creation Error", response.text)
            frappe.msgprint(response.text)

    def initialize_M365_groups_services(self):
        if not self.m365_sharepoint_id or not self.m365_sharepoint_site:
            # added sleep time so the group is properly initialize in MS365 for first itme
            time.sleep(10)

        msg = '''
				<pThe mapping of Frappe modules > M365 Group has started.
                You will be notified once the service is ready to use</p>
			'''
        frappe.msgprint(msg)
        self.create_sharepoint_service()

    def create_sharepoint_service(self):
        if not self.m365_sharepoint_site:
            headers = get_request_header(self._settings)
            url = f'{self._settings.m365_graph_url}/groups/{self.m365_group_id}/sites/root'

            response = make_request('GET', url, headers, None)
            if (response.status_code == 200 or response.ok):
                self.db_set("m365_sharepoint_site", response.json()['webUrl'])
                self.m365_sharepoint_site = response.json()['webUrl']
            else:
                frappe.log_error("sharepoint webUrl error", response.text)
        self.map_sharepoint_id()

    def map_sharepoint_id(self):
        if not self.m365_sharepoint_id:
            headers = get_request_header(self._settings)
            url = f'{self._settings.m365_graph_url}/groups/{self.m365_group_id}/drive/root/children'

            response = make_request('GET', url, headers, None)
            if (response.ok):
                for items in response.json()['value']:
                    if self.name == items["name"]:
                        self.db_set("m365_sharepoint_id", items['id'])
                        self.m365_sharepoint_id = items['id']

            if not self.m365_sharepoint_id:
                headers = get_request_header(self._settings)
                body = {
                    "name": f'{self.name}',
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "rename"
                }
                url = f'{self._settings.m365_graph_url}/groups/{self.m365_group_id}/drive/items'
                response = make_request('POST', url, headers, body)

                if (response.ok):
                    self.db_set("m365_sharepoint_id", response.json()["id"])
                    self.m365_sharepoint_id = response.json()["id"]
                else:
                    frappe.log_error("sharepoint id error", response.text)

        if self.m365_sharepoint_site and self.m365_sharepoint_id:
            frappe.enqueue("frappe_m365.utils.sharepoint.trigger_sharepoint",
                           queue="long", request="MAP", group=self, timeout=-1)
            
    @frappe.whitelist()
    def update_m365_groups_members(self):
        if (self.m365_group_id):
            self._settings = frappe.get_single(M365)
            self.add_members_in_group()
            self.delete_members_in_group()
        elif (not self.group_idm365_group_id):
            frappe.msgprint("Please <b>Connect to M365 Groups</b> first.")

    def get_group_member_list(self):
        """
            fetching M365 Group member list
        """
        members = []
        url = f'{self._settings.m365_graph_url}/groups/{self.m365_group_id}/members'
        headers = get_request_header(self._settings)
        response = make_request('GET', url, headers, None)
        if (response.ok):
            for member in response.json()['value']:
                members.append({"mail": member['mail'], "id": member['id']})
        else:
            frappe.log_error("M365 Group member fetching error", response.text)
        return members

    def get_m365_users_list(self):
        """
            fetching user list with id from organization
        """
        users = []
        url = f'{self._settings.m365_graph_url}/users'
        headers = get_request_header(self._settings)
        headers.update(ContentType)

        response = make_request('GET', url, headers, None)
        if (response.ok):
            for user in response.json()['value']:
                users.append({"mail": user['mail'], "id": user['id']})
        else:
            frappe.log_error("M365 users fetching error", response.text)
        return users

    def add_members_in_group(self):
        """
            checking the listed member(s) exists in the
            organization then adding listed member(s) in
            group if not preset in group member list
        """
        org_users = self.get_m365_users_list()
        org_users_mails = [user['mail'] for user in org_users]
        group_members = self.get_group_member_list()
        group_members_mails = [member['mail'] for member in group_members]

        members_not_in_group = []
        members_not_in_org = []
        for member in self.m365_groups_member:
            mail = member.user
            if mail not in group_members_mails and mail in org_users_mails:
                member_id = ''.join([user['id'] for user in org_users if user['mail'] == mail])
                members_not_in_group.append(f'{self._settings.m365_graph_url}/directoryObjects/{member_id}')
            elif (mail not in org_users_mails):
                members_not_in_org.append(mail)

        if members_not_in_group:
            url = f'{self._settings.m365_graph_url}/groups/{self.m365_group_id}'
            headers = get_request_header(self._settings)
            headers.update(ContentType)
            body = {"members@odata.bind": members_not_in_group}

            response = make_request('PATCH', url, headers, body)
            if not response.ok:
                frappe.log_error("M365 Group member(s) update Error", response.text)
                frappe.msgprint(response.text)
            else:
                frappe.msgprint("Group Member(s) has been updated successfully")
        else:
            frappe.msgprint("Group Member(s) list is up-to date")

        if members_not_in_org:
            msg = """
				<p>At least {0} user(s) is not part of your organization:</p>
				<p><b>{1}</b></p>
				<p>User(s) in this list will not be added to the M365 Group.</p>
			""".format(len(members_not_in_org), "<br>".join(members_not_in_org))
            frappe.msgprint(msg)

    def delete_members_in_group(self):
        delete_member_from_group = []
        group_members = self.get_group_member_list()
        member_data = [member.user for member in self.m365_groups_member]
        for member in group_members:
            if (member['mail'] not in member_data):
                delete_member_from_group.append(member['id'])

        for member in delete_member_from_group:
            url = f'{self._settings.m365_graph_url}/groups/{self.m365_group_id}/members/{member}/$ref'
            headers = get_request_header(self._settings)

            response = make_request('DELETE', url, headers, None)
            if not response.ok:
                frappe.log_error("M365 Group member(s) delete Error", response.text)
