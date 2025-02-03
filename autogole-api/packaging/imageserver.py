from flask import Flask, send_from_directory, render_template_string, abort
import os
import yaml

app = Flask(__name__)

def findImageDirectory():
    config_file = "/etc/rtmon.yaml"
    if not os.path.isfile(config_file):
        raise Exception(f"Config file {config_file} does not exist.")
    try:
        with open(config_file, "r", encoding="utf-8") as fd:
            content = fd.read()
    except Exception as ex:
        raise Exception(f"Error reading the config file: {ex}")

    try:
        config = yaml.safe_load(content)
    except Exception as ex:
        raise Exception(f"Error parsing YAML: {ex}")
    if not isinstance(config, dict):
        raise Exception("Config file does not contain a valid YAML dictionary.")
    image_dir = config.get("image_dir", '/srv/images')
    image_host = config.get("image_host", '0.0.0.0')
    image_port = config.get("image_port", 8000)
    image_debug = config.get("image_debug", True)

    return [image_dir, image_host, image_port, image_debug]

IMAGE_CONFIG = findImageDirectory()
@app.route('/')
def home():
    return "<h1>Hello, this is the root page!</h1>"

@app.route('/images')
def list_images():
    if not os.path.exists(IMAGE_CONFIG[0]):
        return "<h1>Image directory not found.</h1>", 404

    images = [f for f in os.listdir(IMAGE_CONFIG[0]) if os.path.isfile(os.path.join(IMAGE_CONFIG[0], f))]

    html = """
    <h1>Network Topology</h1>
    <ul>
        {% for image in images %}
        <li><a href="/images/{{ image }}">{{ image }}</a></li>
        {% endfor %}
    </ul>
    """
    return render_template_string(html, images=images)

@app.route('/images/<filename>')
def serve_image(filename):
    path = os.path.abspath(os.path.join(IMAGE_CONFIG[0], filename))

    if not path.startswith(IMAGE_CONFIG[0]) or not os.path.isfile(path):
        abort(404)
    return send_from_directory(IMAGE_CONFIG[0], filename)

if __name__ == "__main__":
    app.run(IMAGE_CONFIG[1], IMAGE_CONFIG[2], debug = IMAGE_CONFIG[3])