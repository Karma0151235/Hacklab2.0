@description('Location for all resources')
param location string = resourceGroup().location

@description('Name for the Azure Container App')
param acaName string

@description('Application Insights connection string. Use "DISABLED" to disable telemetry, or provide existing connection string. If omitted, new App Insights will be created.')
param appInsightsConnectionString string = ''

// Deploy Application Insights if appInsightsConnectionString is empty and not DISABLED
var appInsightsName = '${acaName}-insights'

module appInsights 'modules/application-insights.bicep' = {
  name: 'application-insights-deployment'
  params: {
    appInsightsConnectionString: appInsightsConnectionString
    name: appInsightsName
    location: location
  }
}

module acaStorageManagedIdentity 'modules/aca-storage-managed-identity.bicep' = {
  name: 'aca-storage-managed-identity-deployment'
  params: {
    location: location
    managedIdentityName: '${acaName}-storage-managed-identity'
  }
}

// Deploy ACA Infrastructure
module acaInfrastructure 'modules/aca-infrastructure.bicep' = {
  name: 'aca-infrastructure-deployment'
  params: {
    name: acaName
    location: location
    appInsightsConnectionString: appInsights.outputs.connectionString
    azureMcpCollectTelemetry: string(!empty(appInsights.outputs.connectionString))
    namespaces: ['storage'] // Kept for future use
    userAssignedManagedIdentityId: acaStorageManagedIdentity.outputs.managedIdentityId
    userAssignedManagedIdentityClientId: acaStorageManagedIdentity.outputs.managedIdentityClientId
  }
}

// Outputs for azd and other consumers
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_SUBSCRIPTION_ID string = subscription().subscriptionId
output AZURE_RESOURCE_GROUP string = resourceGroup().name
output AZURE_LOCATION string = location

// ACA Infrastructure outputs
output CONTAINER_APP_URL string = acaInfrastructure.outputs.containerAppUrl
output CONTAINER_APP_NAME string = acaInfrastructure.outputs.containerAppName
output AZURE_CONTAINER_APP_ENVIRONMENT_ID string = acaInfrastructure.outputs.containerAppEnvironmentId

// ACA user assigned managed identity
output CONTAINER_APP_MANAGED_IDENTITY_CLIENT_ID string = acaStorageManagedIdentity.outputs.managedIdentityClientId

// Application Insights outputs
output APPLICATION_INSIGHTS_NAME string = appInsightsName
output APPLICATION_INSIGHTS_CONNECTION_STRING string = appInsights.outputs.connectionString
output AZURE_MCP_COLLECT_TELEMETRY string = string(!empty(appInsights.outputs.connectionString))

// Azure AI Foundry
module ai 'modules/ai-foundry.bicep' = {
  name: 'ai-foundry-deployment'
  params: {
    location: location
    name: acaName
    applicationInsightsId: appInsights.outputs.appInsightsId
  }
}

output AI_PROJECT_NAME string = ai.outputs.projectName
output AI_PROJECT_CONNECTION_STRING string = ai.outputs.projectConnectionString
output AZURE_OPENAI_ENDPOINT string = ai.outputs.openaiEndpoint
output AZURE_OPENAI_NAME string = ai.outputs.openaiName
