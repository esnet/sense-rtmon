from flask import Flask, send_from_directory, render_template_string, abort
import os

app = Flask(__name__)

IMAGE_DIRECTORY = '/srv/images'
@app.route('/')
def home():
    return "<h1>Hello, this is the root page!</h1>"

@app.route('/images')
def list_images():
    if not os.path.exists(IMAGE_DIRECTORY):
        return "<h1>Image directory not found.</h1>", 404

    images = [f for f in os.listdir(IMAGE_DIRECTORY) if os.path.isfile(os.path.join(IMAGE_DIRECTORY, f))]

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
    if not os.path.isfile(os.path.join(IMAGE_DIRECTORY, filename)):
        abort(404)
    return send_from_directory(IMAGE_DIRECTORY, filename)

if __name__ == "__main__":
    port = 8000
    app.run(host='0.0.0.0', port=port, debug=True)