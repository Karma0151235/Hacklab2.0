"""
Milvus Vector Database API Routes
Provides REST API access to Milvus collections and stats
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os

router = APIRouter()

# Import Milvus client
try:
    from pymilvus import connections, Collection, utility
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False

# Milvus configuration
MILVUS_HOST = os.getenv('MILVUS_HOST', 'localhost')
MILVUS_PORT = int(os.getenv('MILVUS_PORT', '19639'))

# Collection names
COLLECTIONS = [
    'shareholding_embeddings',
    'financial_embeddings',
    'dividend_embeddings',
    'corporate_embeddings',
    'meeting_embeddings',
    'general_embeddings',
]


class CollectionInfo(BaseModel):
    collectionName: str
    dbName: str = "default"
    loaded: bool = False


class CollectionStats(BaseModel):
    collectionName: str
    rowCount: int
    dataSize: int = 0


class VectorDBStats(BaseModel):
    totalCollections: int
    activeCollections: int
    totalEntities: int
    totalSize: int
    collectionBreakdown: List[CollectionStats]


class QueryRequest(BaseModel):
    collectionName: str
    filter: str = ""
    limit: int = 10
    offset: int = 0
    outputFields: Optional[List[str]] = None


def get_milvus_connection():
    """Get or create Milvus connection"""
    if not MILVUS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Milvus client not available")
    
    try:
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        return True
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Milvus: {str(e)}")


@router.get("/vectordb/collections/list", response_model=List[CollectionInfo])
async def list_collections():
    """List all Milvus collections"""
    get_milvus_connection()
    
    try:
        # Get all collections
        all_collections = utility.list_collections()
        
        result = []
        for col_name in all_collections:
            # Check if collection is loaded
            try:
                col = Collection(col_name)
                loaded = hasattr(col, '_collection') and col._collection is not None
            except:
                loaded = False
            
            result.append(CollectionInfo(
                collectionName=col_name,
                dbName="default",
                loaded=loaded
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.get("/vectordb/collections/{collection_name}/stats", response_model=CollectionStats)
async def get_collection_stats(collection_name: str):
    """Get statistics for a specific collection"""
    get_milvus_connection()
    
    try:
        if not utility.has_collection(collection_name):
            raise HTTPException(status_code=404, detail=f"Collection {collection_name} not found")
        
        collection = Collection(collection_name)
        
        # Get entity count
        num_entities = collection.num_entities
        
        # Estimate data size (rough calculation)
        # Assuming ~10KB per entity on average
        data_size = num_entities * 10240
        
        return CollectionStats(
            collectionName=collection_name,
            rowCount=num_entities,
            dataSize=data_size
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/vectordb/stats", response_model=VectorDBStats)
async def get_vectordb_stats():
    """Get aggregated vector database statistics"""
    get_milvus_connection()
    
    try:
        all_collections = utility.list_collections()
        
        collection_breakdown = []
        total_entities = 0
        total_size = 0
        active_collections = 0
        
        for col_name in all_collections:
            try:
                collection = Collection(col_name)
                num_entities = collection.num_entities
                data_size = num_entities * 10240  # Rough estimate
                
                if num_entities > 0:
                    active_collections += 1
                
                total_entities += num_entities
                total_size += data_size
                
                collection_breakdown.append(CollectionStats(
                    collectionName=col_name,
                    rowCount=num_entities,
                    dataSize=data_size
                ))
            except Exception as e:
                print(f"Error getting stats for {col_name}: {e}")
                collection_breakdown.append(CollectionStats(
                    collectionName=col_name,
                    rowCount=0,
                    dataSize=0
                ))
        
        return VectorDBStats(
            totalCollections=len(all_collections),
            activeCollections=active_collections,
            totalEntities=total_entities,
            totalSize=total_size,
            collectionBreakdown=collection_breakdown
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/vectordb/collections/{collection_name}/describe")
async def describe_collection_endpoint(collection_name: str):
    """Get collection schema"""
    get_milvus_connection()
    
    try:
        if not utility.has_collection(collection_name):
            raise HTTPException(status_code=404, detail=f"Collection {collection_name} not found")
        
        collection = Collection(collection_name)
        schema = collection.schema
        
        # Convert schema to dict
        fields = []
        for field in schema.fields:
            fields.append({
                "name": field.name,
                "type": str(field.dtype),
                "is_primary": field.is_primary,
                "description": field.description or ""
            })
        
        return {
            "collectionName": collection_name,
            "description": schema.description,
            "fields": fields
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to describe collection: {str(e)}")


@router.post("/vectordb/entities/query")
async def query_entities_endpoint(request: QueryRequest):
    """Query entities from a collection"""
    get_milvus_connection()
    
    try:
        if not utility.has_collection(request.collectionName):
            raise HTTPException(status_code=404, detail=f"Collection {request.collectionName} not found")
        
        collection = Collection(request.collectionName)
        collection.load()
        
        # Default output fields if not specified
        output_fields = request.outputFields if request.outputFields else ["*"]
        
        # Query
        # For Milvus, we need a valid expression. To get all, we can use a tautology
        # or just specify limit without expression
        try:
            if request.filter:
                results = collection.query(
                    expr=request.filter,
                    output_fields=output_fields,
                    limit=request.limit,
                    offset=request.offset
                )
            else:
                # Get primary key field name
                pk_field = None
                for field in collection.schema.fields:
                    if field.is_primary:
                        pk_field = field.name
                        break
                
                if pk_field:
                    # Use a tautology: pk >= "" or pk != ""
                    results = collection.query(
                        expr=f'{pk_field} != ""',
                        output_fields=output_fields,
                        limit=request.limit,
                        offset=request.offset
                    )
                else:
                    # Fallback to empty result if no PK found
                    results = []
        except Exception as query_error:
            print(f"Query error: {str(query_error)}")
            # Fallback: return empty list on query error
            results = []
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Failed to query entities: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to query entities: {str(e)}")


@router.get("/vectordb/health")
async def vectordb_health():
    """Check Milvus connection health"""
    try:
        get_milvus_connection()
        collections = utility.list_collections()
        return {
            "status": "healthy",
            "connected": True,
            "host": MILVUS_HOST,
            "port": MILVUS_PORT,
            "collections_count": len(collections)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }
