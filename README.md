<div align="center">
    <a href="http://aptitudetech.net/">
        <img src="https://22698e.p3cdn1.secureserver.net/wp-content/uploads/2017/05/Logo_AptitudeTechnologies.png" height="128">
    </a>
    <h2>Aptitude Technologies</h2>
</div>

## Microsoft 365 Groups

<p>Groups in Microsoft 365 let you choose a set of people that you wish to collaborate with and easily set up a collection of resources for those people to share. Resources such as a shared Outlook inbox, shared calendar or a document library for collaborating on files.</p>

## Group types in Azure AD and Microsoft Graph

<p>Groups are collections of principals with shared access to resources in Microsoft services or in your app. Different principals such as users, other groups, devices, and applications can be part of groups.</p>

<p>Azure Active Directory (Azure AD) supports the following types of groups.</p>

1. Microsoft 365 groups
2. Security groups
3. Mail-enabled security groups
4. Distribution groups

<p>Note: Only the Microsoft 365 groups type can be managed through our app right now.</p>

---

## Main Features

1. Create and Manage multiple MS 365 Groups
2. Manage Group Members
3. One SharePoint site per Group
4. Manage file storage
5. Supports Version 13 and Version 14

### How to Install

#### Self Hosting:

1. `bench get-app https://github.com/Aptitudetech/frappe-m365.git`
2. `bench --site [your.site.name] install-app frappe-m365`
3. `bench --site [your.site.name] migrate`
4. `bench restart`

---

### Bug report:

Please Create Github Issue [here](https://github.com/Aptitudetech/frappe-m365/issues/new)

---

### Dependencies:

- [Frappe](https://github.com/frappe/frappe)

---

### Setup and Use:

#### In Frappe M365

1. Go to → M365 Groups 
    
    Enter Group Information
    
    - When creating an M365 Group, if no Group Members are specified, the Group will be created without specific permissions.
    - When a user is associated with the Group, user added as a member in the Group.  Afterward, if a user is removed from the Group, it will be also removed from the Group

<img src="https://user-images.githubusercontent.com/16163737/228617772-e58d0618-7a3c-4ae4-b08a-e415e78d0a2a.png" height="480">

2. Go to → M365 Groups Settings ->
    
    Setup and define following settings:

    1. App Oauth Information.
    2. Enable and Disable file sync.
        - Only new files will be synchronized.
    3. Replace File Link with SharePoint site web url.
        - If unchecked, file will reside on both sides.
        - If checked, file resides ONLY in SharePoint.
    4. Default Group for all your files.
        - Default group with which files will be synchronized.
    5. Module Settings:
        1. Define Module and Default Group for file sync.
        2. Add Role based file sync.
        
        - On this table, the app provides the flexibility to override the "Default M365 Group" and configure specific Group per Module.
        - If the user(s) is not the part of your Organization, those user(s) will not be added to the M365 group
        - If a Role is specified, only users part of this role will synchronize over the specified group. Other users will default to the "Default M365 Group".
        - If a Role is selected, Default Group is mentioned and Update User(s) is clicked, all the user(s) having that role will become the members of that Group.

<img src="https://user-images.githubusercontent.com/16163737/228869566-9a88848c-908e-462a-950b-b6db17f8f622.png" height="480">


#### In Microsoft Azure Active Directory

1. Go to → Your Azure Portal -> Create New App Registration and use it for Connected Apps

<img src="https://user-images.githubusercontent.com/16163737/228617348-116fec64-ce96-4337-bed8-c6b2f2ec7340.png" height="480">

2. Add some extra delegated permissions in your App permissions list
    1. offline_access
    2. Files.ReadWrite.All
    3. Sites.FullControl.All
    4. User.Read.All
    5. Group.ReadWrite.All

---

### License

MIT
