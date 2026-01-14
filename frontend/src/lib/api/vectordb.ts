import {
  VectorCollection,
  CollectionStats,
  VectorSearchResult,
  VectorEntity,
} from '@/lib/types/api'

/**
 * Milvus Vector Database API Client
 * Connects to backend API proxy for Milvus operations
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

// Known collections in the system
export const COLLECTION_NAMES = [
  'shareholding_embeddings',
  'financial_embeddings',
  'dividend_embeddings',
  'corporate_embeddings',
  'meeting_embeddings',
  'general_embeddings',
] as const

export type CollectionName = typeof COLLECTION_NAMES[number]

/**
 * Authentication configuration
 * Set these in your .env.local file if authentication is enabled
 */
const AUTH_ENABLED = process.env.NEXT_PUBLIC_MILVUS_AUTH_ENABLED === 'true'
const AUTH_TOKEN = process.env.NEXT_PUBLIC_MILVUS_TOKEN

/**
 * Create headers with optional authentication
 */
function createHeaders(): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  if (AUTH_ENABLED && AUTH_TOKEN) {
    headers['Authorization'] = `Bearer ${AUTH_TOKEN}`
  }

  return headers
}

/**
 * List all collections in the vector database
 */
export async function listCollections(): Promise<VectorCollection[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/vectordb/collections/list`, {
      method: 'GET',
      headers: createHeaders(),
    })

    if (!response.ok) {
      throw new Error(`Failed to list collections: ${response.statusText}`)
    }

    const data = await response.json()
    return data || []
  } catch (error) {
    console.error('Error listing collections:', error)
    // Return mock data if API is unavailable
    return COLLECTION_NAMES.map(name => ({
      collectionName: name,
      dbName: 'default',
      loaded: false,
    }))
  }
}

/**
 * Get collection statistics
 */
export async function getCollectionStats(collectionName: string): Promise<CollectionStats | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/vectordb/collections/${collectionName}/stats`, {
      method: 'GET',
      headers: createHeaders(),
    })

    if (!response.ok) {
      throw new Error(`Failed to get stats for ${collectionName}: ${response.statusText}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error(`Error getting stats for ${collectionName}:`, error)
    return null
  }
}

/**
 * Get all collection statistics
 */
export async function getAllCollectionStats(): Promise<CollectionStats[]> {
  const collections = await listCollections()
  const statsPromises = collections.map(col => getCollectionStats(col.collectionName))
  const stats = await Promise.all(statsPromises)
  return stats.filter((s): s is CollectionStats => s !== null)
}

/**
 * Describe collection schema
 */
export async function describeCollection(collectionName: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/vectordb/collections/${collectionName}/describe`, {
      method: 'GET',
      headers: createHeaders(),
    })

    if (!response.ok) {
      throw new Error(`Failed to describe ${collectionName}: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error(`Error describing ${collectionName}:`, error)
    return null
  }
}

/**
 * Load a collection into memory
 */
export async function loadCollection(collectionName: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/vectordb/collections/load`, {
      method: 'POST',
      headers: createHeaders(),
      body: JSON.stringify({ collectionName }),
    })

    if (!response.ok) {
      throw new Error(`Failed to load ${collectionName}: ${response.statusText}`)
    }

    return true
  } catch (error) {
    console.error(`Error loading ${collectionName}:`, error)
    return false
  }
}

/**
 * Query entities from a collection
 */
export async function queryEntities(
  collectionName: string,
  options: {
    filter?: string
    limit?: number
    offset?: number
    outputFields?: string[]
  } = {}
): Promise<VectorEntity[]> {
  try {
    const {
      filter = '',
      limit = 10,
      offset = 0,
      outputFields = ['chunk_id', 'doc_id', 'content', 'company_code', 'document_type', 'chunk_order'],
    } = options

    const response = await fetch(`${API_BASE_URL}/api/v1/vectordb/entities/query`, {
      method: 'POST',
      headers: createHeaders(),
      body: JSON.stringify({
        collectionName,
        filter,
        limit,
        offset,
        outputFields,
      }),
    })

    if (!response.ok) {
      throw new Error(`Failed to query ${collectionName}: ${response.statusText}`)
    }

    const data = await response.json()
    return data || []
  } catch (error) {
    console.error(`Error querying ${collectionName}:`, error)
    return []
  }
}

/**
 * Search for similar vectors
 */
export async function searchVectors(
  collectionName: string,
  queryEmbedding: number[],
  options: {
    limit?: number
    outputFields?: string[]
  } = {}
): Promise<VectorSearchResult[]> {
  try {
    const {
      limit = 5,
      outputFields = ['chunk_id', 'doc_id', 'content', 'company_code', 'document_type'],
    } = options

    const response = await fetch(`${API_BASE_URL}/api/v1/vectordb/entities/search`, {
      method: 'POST',
      headers: createHeaders(),
      body: JSON.stringify({
        collectionName,
        data: [queryEmbedding],
        annsField: 'embedding',
        limit,
        outputFields,
      }),
    })

    if (!response.ok) {
      throw new Error(`Failed to search ${collectionName}: ${response.statusText}`)
    }

    const data = await response.json()
    return data.data || []
  } catch (error) {
    console.error(`Error searching ${collectionName}:`, error)
    return []
  }
}

/**
 * Get aggregated vector database statistics
 */
export async function getVectorDBStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/vectordb/stats`, {
      method: 'GET',
      headers: createHeaders(),
    })

    if (!response.ok) {
      throw new Error(`Failed to get stats: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error getting vector DB stats:', error)
    // Return mock data
    const stats = await getAllCollectionStats()
    const totalEntities = stats.reduce((sum, s) => sum + s.rowCount, 0)
    const totalSize = stats.reduce((sum, s) => sum + (s.dataSize || 0), 0)
    const activeCollections = stats.filter(s => s.rowCount > 0).length

    return {
      totalCollections: stats.length,
      activeCollections,
      totalEntities,
      totalSize,
      collectionBreakdown: stats,
    }
  }
}

/**
 * Check if a collection has data
 */
export async function hasCollectionData(collectionName: string): Promise<boolean> {
  const stats = await getCollectionStats(collectionName)
  return stats ? stats.rowCount > 0 : false
}
