
#!/usr/bin/env python3
"""
Azure Startup Script for CV Optimizer Pro
Uruchamia aplikację na Azure App Service
"""

import os
import sys
import logging
from app import app

# Configure logging for Azure
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/app.log')
    ]
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # Azure App Service port
    port = int(os.environ.get('PORT', 8000))
    
    logger.info(f"Starting CV Optimizer Pro on port {port}")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    # Bind to all interfaces for Azure
    app.run(host='0.0.0.0', port=port, debug=False)
