import re
from datetime import datetime
from typing import Optional

def normalize_date(date_str: str) -> Optional[str]:
    """
    Normalize various date formats to YYYY-MM-DD.
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    formats = [
        '%d %b %Y',      # 14 Jan 2026
        '%Y-%m-%d',      # 2026-01-14
        '%d/%m/%Y',      # 14/01/2026
        '%m/%d/%Y',      # 01/14/2026
        '%d-%m-%Y',      # 14-01-2026
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
            
    return None

def clean_html(raw_html: str) -> str:
    """
    Basic HTML cleaning to reduce noise before storage.
    Removes script and style tags.
    """
    clean = re.sub(r'<script\b[^>]*>([\s\S]*?)</script>', '', raw_html)
    clean = re.sub(r'<style\b[^>]*>([\s\S]*?)</style>', '', clean)
    return clean

def extract_company_name(text: str) -> Optional[str]:
    """
    Simple heuristic to extract company name if standard fields fail.
    """
    # Placeholder for more complex logic
    return None
