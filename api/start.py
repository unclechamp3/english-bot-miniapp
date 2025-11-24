"""
Startup script for Render deployment.
Adds parent directory to path so we can import 'services' module.
"""

import sys
from pathlib import Path
import os

# Add parent directory to Python path to access 'services' module
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Now we can import uvicorn and start the server
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

