from flask import Flask, jsonify, request
from flask_cors import CORS
import base64
from PIL import Image
import cv2
import numpy as np
import clip
import torch

app = Flask(__name__)
# Neccessary to prevent CORS error being thrown.
# https://stackoverflow.com/questions/28461001/python-flask-cors-issue
CORS(app)

# Set up clip model.
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-L/14", device=device, jit=True)


@app.route('/')
def index():
    return "Success"


@app.route('/get_embedding', methods=["POST"])
def process_image():
    """_summary_
    This function is called when a request is made to the /get_embedding endpoint. It receives an image and returns a clip
    image embedding of that image. If there is no image data is present in the request, it returns 
    {'success': 'False', 'msg': 'No image found in request'}.

    If the a clip embedding is successfully generated, it returns {'success': 'True', 'embedding': embedding.tolist()}

    If there was an error generating the embedding, it returns {'success': 'False', 'msg': 'Error Processing Image'}
    """
    try:
        req = request.get_json()
        if "img" not in req:
            return jsonify({'success': 'False', 'msg': 'No image found in request'}), 400

        raw_content = req["img"]
        decoded_string = base64.b64decode(raw_content)
        numpy_image = np.frombuffer(decoded_string, dtype=np.uint8)

        # Decode the image data from the numpy array
        img = cv2.imdecode(numpy_image, cv2.IMREAD_UNCHANGED)
        img = Image.fromarray(img)

        # Get embedding
        embedding = generate_embedding(img)
        return jsonify({'success': 'True', 'embedding': embedding.tolist()}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': 'False', 'msg': 'Error Processing Image'}), 500


def generate_embedding(img):
    """_summary_
    This function receives an image object and returns a clip image embedding.
    """
    prepro = preprocess(img).unsqueeze(0).to(device)
    with torch.no_grad():
        image_features = model.encode_image(prepro)
        # moves image features tensor from GPU to CPU if it is currently on GPU and casts as float.
        emb = image_features.to("cpu").float()
        # emb = image_features.cpu().detach().numpy().astype("float32")
    return emb


if __name__ == "__main__":
    app.run(debug=True, port=5002)
