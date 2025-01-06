import matplotlib
matplotlib.use('Agg')  # GUI 비활성화

from flask import Flask, request, jsonify, render_template
import numpy as np
import cv2
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import io
import base64
from PIL import Image
import colorsys
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def extract_colors(image, k):
    pixel_data = image.reshape((-1, 3))
    kmeans = KMeans(n_clusters=k, random_state=0)
    kmeans.fit(pixel_data)
    colors = kmeans.cluster_centers_
    return colors

def plot_colors(colors, image, k):
    fig, ax = plt.subplots(1, 2, figsize=(15, 7))
    ax[0].imshow(image)
    ax[0].axis('off')
    ax[0].set_title('Original Image')

    bar = np.zeros((50, 300, 3), dtype='uint8')
    width = 300 // k
    for i in range(k):
        bar[:, i*width:(i+1)*width] = colors[i]

    ax[1].imshow(bar)
    ax[1].axis('off')
    ax[1].set_title('Dominant Colors')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()

    return base64.b64encode(image_png).decode('utf-8')

def rgb_to_hsv(rgb):
    rgb = np.array(rgb, dtype='float') / 255.0
    hsv = colorsys.rgb_to_hsv(rgb[0], rgb[1], rgb[2])
    hsv = np.array(hsv) * np.array([360, 100, 100])
    return hsv

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('images')
    k = int(request.form['k'])
    results = []

    for file in files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        image = cv2.imread(file_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        colors = extract_colors(image, k)
        colors = colors.astype(int).tolist()
        image_data = plot_colors(colors, image, k)
        results.append({'image': image_data, 'colors': colors})

        os.remove(file_path)

    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(debug=True, port=5000)  # 포트를 5000으로 변경

