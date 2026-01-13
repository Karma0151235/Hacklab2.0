# Centralized selectors for Bursa Malaysia scraping
SELECTORS = {
    "listing_page_url": "https://bursa-bm.listedcompany.com/newsroom.html",
    
    # Listing Page
    "announcement_rows": "tr.bm_row1, tr.bm_row2",
    #"announcement_date": "td:nth-child(1), [data-date], .date", # Varies by format, stick to generic querySelector
    
    # Valid selectors for extracting columns in listing (heuristic index based)
    
    # Detail Page
    "table_elements": "table",
    "paragraph_content": "p, .content-text, .announcement-body p",
    
    # PDF
    "pdf_links": "a[href*='.pdf'], .pdf a",
}
