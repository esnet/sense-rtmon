#!/usr/bin/env python3
"""Image Server for RTMon which runs an HTTP endpoint to serve images"""

import os
from flask import Flask, send_from_directory, render_template_string, abort
from RTMonLibs.GeneralLibs import getConfig

class ImageServer:
    """Encapsulates the image server functionality"""

    def __init__(self):
        """Initialize the ImageServer"""
        self.app = Flask(__name__)
        self.config = getConfig()
        self.setConfigDefaults()
        self.setupRoutes()

    def setConfigDefaults(self):
        """Load configuration settings"""
        self.config.setdefault("image_dir", "/srv/images")
        self.config.setdefault("image_host", "0.0.0.0")
        self.config.setdefault("image_port", 8000)
        self.config.setdefault("image_debug", False)

    def setupRoutes(self):
        """Define the routes for the Flask app"""

        @self.app.route("/")
        def home():
            """Home page"""
            return "<h1>Hello, this is the root page!</h1>"

        @self.app.route("/images")
        def list_images():
            """List images in the directory"""
            imageDir = self.config["image_dir"]
            if not os.path.exists(imageDir):
                print("Image directory does not exist.")
                return "<h1>Image directory not found.</h1>", 404

            images = [f for f in os.listdir(imageDir) if os.path.isfile(os.path.join(imageDir, f))]
            html = """
            <h1>Network Topology</h1>
            <ul>
                {% for image in images %}
                <li><a href="/images/{{ image }}">{{ image }}</a></li>
                {% endfor %}
            </ul>
            """
            return render_template_string(html, images=images)

        @self.app.route("/images/<filename>")
        def serve_image(filename):
            """Serve an image if it exists"""
            imageDir = self.config["image_dir"]
            path = os.path.abspath(os.path.join(imageDir, filename))
            if not path.startswith(imageDir) or not os.path.isfile(path):
                print(f"File not found: {filename}")
                abort(404)
            return send_from_directory(imageDir, filename)

    def run(self):
        """Run the Flask application"""
        self.app.run(
            host=self.config["image_host"],
            port=self.config["image_port"],
            debug=self.config["image_debug"]
        )

def main():
    """Main function"""
    mainserver.run()

mainserver = ImageServer()
app = mainserver.app

if __name__ == "__main__":
    main()
