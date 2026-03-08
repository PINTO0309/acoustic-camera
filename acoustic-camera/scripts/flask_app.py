from flask import Flask, render_template, Response
import cv2
from bokeh.embed import server_document
import os
from config import ConfigManager, apply_runtime_camera_config


app = Flask(__name__,
            template_folder=os.path.abspath("templates"))

CONFIG_PATH = "config/config.json"
config = ConfigManager(CONFIG_PATH)

camera_width = os.environ.get("ACOUSTIC_CAMERA_CAMERA_WIDTH")
camera_height = os.environ.get("ACOUSTIC_CAMERA_CAMERA_HEIGHT")
camera_ratio = apply_runtime_camera_config(
    config,
    int(camera_width) if camera_width else None,
    int(camera_height) if camera_height else None,
)

@app.route('/video_feed')
def video_feed():
    def gen_frames():
        cap = cv2.VideoCapture(0)
        if camera_width and camera_height:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(camera_width))
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(camera_height))
        while True:
            success, frame = cap.read()
            if not success:
                break
            else:
                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    bokeh_script = server_document("http://localhost:5006/bokeh_app")
    return render_template('index.html', bokeh_script=bokeh_script, json_data=config._config)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
