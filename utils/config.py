"""Application configuration and settings"""

class Config:
    # Flask settings
    HOST = '0.0.0.0'
    PORT = 8080
    DEBUG = True
    
    # Kubernetes settings
    NAMESPACE_CACHE_TTL = 300  # 5 minutes
    POD_CACHE_TTL = 60        # 1 minute
    EVENT_CACHE_TTL = 30      # 30 seconds
    
    # UI settings
    ITEMS_PER_PAGE = 50
    MAX_EVENTS = 100
