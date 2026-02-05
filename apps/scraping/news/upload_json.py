"""
Upload existing JSON file to Supabase
Usage: uv run python -m scraping.news.upload_json <json_file_path>
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scraping.news.schemas import NewsArticle
from scraping.news.supabase_client import store_articles, test_connection

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python -m scraping.news.upload_json <json_file_path>")
        sys.exit(1)
    
    json_file = Path(sys.argv[1])
    
    if not json_file.exists():
        print(f"❌ File not found: {json_file}")
        sys.exit(1)
    
    print("=" * 60)
    print(f"UPLOADING: {json_file.name}")
    print("=" * 60)
    
    # Test connection first
    if not test_connection():
        print("\n❌ Connection test failed - aborting upload")
        sys.exit(1)
    
    # Load JSON
    print(f"\nLoading articles from {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        articles_data = json.load(f)
    
    print(f"Found {len(articles_data)} articles")
    
    # Convert to NewsArticle objects
    articles = []
    for data in articles_data:
        # Parse published_date if it's a string
        if isinstance(data.get('published_date'), str):
            try:
                data['published_date'] = datetime.fromisoformat(data['published_date'])
            except:
                data['published_date'] = None
        
        # Remove scraped_at and tickers_mentioned if present
        data.pop('scraped_at', None)
        data.pop('tickers_mentioned', None)
        
        articles.append(NewsArticle(**data))
    
    # Store in Supabase
    print(f"\nUploading to Supabase...")
    stored = store_articles(articles)
    
    print("=" * 60)
    print(f"✅ Upload complete: {stored}/{len(articles)} articles stored")
    print("=" * 60)

if __name__ == "__main__":
    main()
