@description('Azure Region')
param location string = resourceGroup().location

@description('Suffix to append to resource names for uniqueness')
param resourceSuffix string = uniqueString(resourceGroup().id)

@description('Name prefix')
param name string = 'ai-foundry'

@description('Application Insights Resource ID')
param applicationInsightsId string

@description('Key Vault Resource ID (optional, will create if not provided)')
param keyVaultId string = ''

@description('Storage Account Resource ID (optional, will create if not provided)')
param storageAccountId string = ''

var cleanName = replace(name, '-', '')

// 1. Dependent Resources (Storage + KeyVault) if not provided
resource storage 'Microsoft.Storage/storageAccounts@2022-09-01' = if (empty(storageAccountId)) {
  name: 'st${take(cleanName, 15)}${take(resourceSuffix, 5)}'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}

resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' = if (empty(keyVaultId)) {
  name: 'kv-${take(name, 15)}-${take(resourceSuffix, 5)}'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: []
    enableRbacAuthorization: true
  }
}

var finalStorageId = empty(storageAccountId) ? storage.id : storageAccountId
var finalKeyVaultId = empty(keyVaultId) ? keyVault.id : keyVaultId

// 2. Azure OpenAI Account
resource openai 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: 'aoai-${name}-${resourceSuffix}'
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: 'aoai-${name}-${resourceSuffix}'
  }
}

// 3. AI Hub (Machine Learning Workspace)
resource hub 'Microsoft.MachineLearningServices/workspaces@2023-08-01-preview' = {
  name: 'hub-${name}-${resourceSuffix}'
  location: location
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  kind: 'Hub'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'AI Foundry Hub'
    storageAccount: finalStorageId
    keyVault: finalKeyVaultId
    applicationInsights: !empty(applicationInsightsId) ? applicationInsightsId : null
    hbiWorkspace: false
  }
}

// 4. AI Project
resource project 'Microsoft.MachineLearningServices/workspaces@2023-08-01-preview' = {
  name: 'proj-${name}-${resourceSuffix}'
  location: location
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'Market Intelligence Project'
    hubResourceId: hub.id
  }
}

// 5. Connections (Link OpenAI to Hub)
resource openaiConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01-preview' = {
  parent: hub
  name: 'aoai-connection'
  properties: {
    category: 'AIServices'
    target: openai.properties.endpoint
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: openai.id
    }
  }
}

// Outputs
output projectConnectionString string = project.properties.discoveryUrl
output projectName string = project.name
output hubName string = hub.name
output openaiEndpoint string = openai.properties.endpoint
output openaiName string = openai.name
