# /home/ubuntu/reddit_dashboard/src/main.py

import sys
import os

# Add project root to Python path - DO NOT CHANGE THIS LINE
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
# Import the function that creates the Dash app
from src.dashboard import create_dashboard

# Initialize Flask server
server = Flask(__name__)

# Database configuration (currently disabled, keep commented unless needed)
# server.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{os.getenv("DB_USERNAME", "root")}:{os.getenv("DB_PASSWORD", "password")}@{os.getenv("DB_HOST", "localhost")}:{os.getenv("DB_PORT", "3306")}/{os.getenv("DB_NAME", "mydb")}"
# server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# db.init_app(server)

# Create and configure the Dash app, passing the Flask server instance
dash_app = create_dashboard(server)

# Optional: Add a simple Flask route for health check or basic info
@server.route("/_health")
def health_check():
    return "Flask server is running."

# Run the Flask server which will also serve the Dash app
if __name__ == "__main__":
    # Important: Use 0.0.0.0 to make the server accessible externally
    # Use a standard port like 8050 for Dash apps
    server.run(host="0.0.0.0", port=8050, debug=False) # Set debug=False for production/testing

