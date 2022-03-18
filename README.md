# Collect Tenant Activity Logs

Microsoft Azure records platform-level events to the [Activity Log](https://docs.microsoft.com/en-us/azure/azure-monitor/essentials/activity-log). The Activity Log will contain events related to the creation, modification, and deletion of Azure resources. Examples include the creation of a role assignment or modification of a Virtual Machine's network interface. It is critical for organizations to preserve and analyze these logs to maintain the security of the Azure platform.

Microsoft public documentation focuses on Activity Logs at the subcription scope. However, there are also Activity Logs at the [Management Group](https://journeyofthegeek.com/2019/10/17/capturing-azure-management-group-activity-logs-using-azure-automation-part-1/) and [Tenant](https://docs.microsoft.com/en-us/rest/api/monitor/tenant-activity-logs) scope. Manag


This PowerShell script is designed to run an an [Azure Automation Runbook](https://docs.microsoft.com/en-us/azure/automation/automation-runbook-types#powershell-runbooks).  The script collects the Activity Logs associated with each [Management Group](https://docs.microsoft.com/en-us/azure/governance/management-groups/overview) within an Azure Active Directory tenant and writes the logs to blob storage in an Azure Storage Account.  It additionally can deliver the logs to an Azure Event Hub and Azure Monitor through the [Azure Monitor HTTP Data Collector API](https://docs.microsoft.com/en-us/azure/azure-monitor/platform/data-collector-api).  The log created in Azure Monitor is named mgmtGroupActivityLogs.

You can find a detailed write up of the process I used to put this together on my [blog](https://journeyofthegeek.com/2019/10/17/capturing-azure-management-group-activity-logs-using-azure-automation-part-1/).  The write up includes API endpoints you'll need to use that aren't well documented in official Microsoft documentation.

## What problem does this solve?
In Microsoft Azure, write, update, and delete operations on the cloud control plane are logged to the [Azure Activity Log](https://docs.microsoft.com/en-us/azure/azure-monitor/platform/activity-logs-overview).  Each Azure Subscription and Azure Management Group have an Activity Log which are retained on the platform for 90 days.  To retain the logs for more than 90 days the logs need to be retrieved and stored in another medium.  Activity Logs for subscriptions have been integrated with [Azure Storage, Azure Log Analytics, and Azure Event Hubs](https://docs.microsoft.com/en-us/azure/azure-monitor/platform/activity-log-export).  The logs for Management Groups are only accessible through the [Azure Portal and the Azure REST API](https://feedback.azure.com/forums/911473-azure-management-groups/suggestions/34705756-activity-log-for-management-group), and as of October 2019, have not yet been integrated with other storage mediums. 

Management Groups were introduced to Microsoft Azure as a means of applying governance and access controls across multiple Azure Subscriptions.  This is accomplished through the use of [Azure Policy](https://docs.microsoft.com/en-us/azure/governance/policy/overview) and [Azure RBAC](https://docs.microsoft.com/en-us/azure/role-based-access-control/overview).  This means that activites performed on management groups need to be monitored, analyzed, and alerted upon.

This Runbook can be used to collect the Activity Logs from all Management Groups within an Azure AD Tenant in order to retain, analyze, and alert on the logs.  It will write the logs to blob storage in an Azure Storage Account and optionally to a Log Analytics Workspace and Azure Event Hub.  

## Requirements

### Azure Identity and Access Management Requirements
The following Azure RBAC Roles must be granted to the Azure Automation Account under the context which the Runbook runs.

* [Reader](https://docs.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#reader) on Tenant Root Group Management Group
* [Storage Blob Contributor](https://docs.microsoft.com/en-us/azure/storage/common/storage-auth-aad-rbac-portal) on the Azure Storage Account where you want to write the logs

### Azure Resource Requirements
* Azure Storage Account with a container already created for the blobs
* (Optional) Azure Log Analytics Workspace
* (Optional) Azure Event Hub

### .NET Libraries
The following .NET libraries need to be [imported](https://docs.microsoft.com/en-us/azure/automation/shared-resources/modules) into the Azure Automation Account.  You can use the command line version of [Nuget](https://www.nuget.org/downloads).  Each library needs to be packed into a separate ZIP file for important.  Ensure you capture both the DLL and XML/PDB (if present) files for each package.

* [Microsoft.IdentityModel.Clients.ActiveDirectory 5.2.3](https://www.nuget.org/packages/Microsoft.IdentityModel.Clients.ActiveDirectory/)
* [Microsoft.Azure.EventHubs 4.1.0 - .NET Standard 2.0](https://www.nuget.org/packages/Microsoft.Azure.EventHubs/)
* [Microsoft.Azure.Amqp 2.4.3](https://www.nuget.org/packages/Microsoft.Azure.Amqp/2.4.3)
* [System.Diagnostics.DiagnosticSource 4.6.0 - .NET 4.5](https://www.nuget.org/packages/System.Diagnostics.DiagnosticSource/)

## Setup

1. Create a new [Azure Automation Account](https://docs.microsoft.com/en-us/azure/automation/automation-quickstart-create-account)
2. Install and run the [Update-AutomationAzureModulesForAccount](https://github.com/microsoft/AzureAutomation-Account-Modules-Update/blob/master/Update-AutomationAzureModulesForAccount.ps1) PowerShell runbook.
3. [Install](https://docs.microsoft.com/en-us/azure/automation/shared-resources/modules) the .NET modules referenced above into the Azure Automation Account.
4. Create the required Azure resources above and optional resources if choosing to write to Azure Monitor or Azure Event Hub.
5. Grant the RBAC roles referenced in the requirements above to the service principal used by the Azure Automation Account.
6. Create three [variables](https://docs.microsoft.com/en-us/azure/automation/shared-resources/variables) in the Azure Automation Account.  The variables should be named and used as follows:
  * eventHubConnString - Connection string for the Event Hub you want the logs to stream to.
  * logAnalyticsWorkspaceId - Log Analytics Workspace Id you want the logs to be sent to.
  * logAnalyticsWorkspaceKey- Log Analytics Workspace Key you want the logs to be sent to.
7. Install the Collect-ManagementGroupActivityLogs
8. Run on demand, [schedule](https://docs.microsoft.com/en-us/azure/automation/shared-resources/schedules), or whatever floats your boat!


