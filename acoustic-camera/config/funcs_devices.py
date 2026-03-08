import sounddevice as sd
import numpy as np
import csv
import os

try:
    import cv2
except ImportError:  # pragma: no cover - optional dependency at runtime
    cv2 = None


def get_uma16_index():
    """
    Get the index of the UMA-16 microphone array.

    Returns:
        int: Index of the UMA-16 microphone array if found, otherwise None.
    """
    devices = sd.query_devices()
    device_index = None
    generic_device_names = {
        "sysdefault",
        "default",
        "pulse",
        "dmix",
        "front",
        "surround40",
        "surround51",
        "surround71",
    }

    # Look for UMA-16 by various possible names
    uma16_names = ["nanoSHARC micArray16", "UMA16v2", "UMA16", "UMA-16"]

    for index, device in enumerate(devices):
        device_name = device["name"]
        input_channels = device.get("max_input_channels", 0)
        for uma_name in uma16_names:
            if uma_name in device_name and input_channels >= 16:
                device_index = index
                print(
                    f"\nUMA-16 input device found: {device_name} "
                    f"at index {device_index} ({input_channels} input channels)\n"
                )
                return device_index

    # If not found by name, prefer non-generic devices with exactly 16 input channels.
    for index, device in enumerate(devices):
        device_name = device["name"]
        input_channels = device.get('max_input_channels', 0)
        normalized_name = device_name.strip().lower()
        if input_channels == 16 and normalized_name not in generic_device_names:
            device_index = index
            print(
                f"\nUMA-16-compatible input device detected by channel count: "
                f"{device_name} at index {device_index} "
                f"({input_channels} input channels)\n"
            )
            return device_index

    # Last fallback: any non-generic multi-channel input device.
    for index, device in enumerate(devices):
        device_name = device["name"]
        input_channels = device.get('max_input_channels', 0)
        normalized_name = device_name.strip().lower()
        if input_channels >= 16 and normalized_name not in generic_device_names:
            device_index = index
            print(
                f"\nFallback multi-channel input device detected: "
                f"{device_name} at index {device_index} "
                f"({input_channels} input channels)\n"
            )
            return device_index

    print("Could not find the UMA-16 device.")
    return device_index


def load_calibration_data(csv_file):
    """
    Load camera calibration data from a CSV file.

    This function reads a CSV file containing camera calibration data, including
    the camera matrix, distortion coefficients, rotation vectors, and translation vectors.

    Args:
        csv_file (str): Path to the CSV file containing the calibration data.

    Returns:
        tuple:
            - numpy.ndarray: Camera matrix (3x3).
            - numpy.ndarray: Distortion coefficients.
            - list: Rotation vectors (list of 3x1 numpy arrays).
            - list: Translation vectors (list of 3x1 numpy arrays).
    """
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        data = list(reader)

        # Parse camera matrix and distortion coefficients
        camera_matrix = np.array(data[0][1:], dtype=np.float32).reshape((3, 3))
        dist_coeffs = np.array(data[1][1:], dtype=np.float32)

        # Parse rotation and translation vectors
        r_vecs = []
        t_vecs = []
        for i in range(2, len(data), 2):
            r_vec = np.array(data[i][1:], dtype=np.float32).reshape((3, 1))
            t_vec = np.array(data[i + 1][1:], dtype=np.float32).reshape((3, 1))
            r_vecs.append(r_vec)
            t_vecs.append(t_vec)

    return camera_matrix, dist_coeffs, r_vecs, t_vecs


def calculate_alphas(ratio=(4, 3), dx=None, dy=None, dz=None):
    """
    Calculate the field of view angles (alphas) based on the camera's aspect ratio and dimensions.

    Args:
        ratio (tuple): Aspect ratio of the camera (default is (4, 3)).
        dx (float, optional): Width of the field of view.
        dy (float, optional): Height of the field of view.
        dz (float): Distance from the camera to the object plane.

    Returns:
        tuple:
            - float: Horizontal field of view angle (alpha_x) in radians.
            - float: Vertical field of view angle (alpha_y) in radians.

    Raises:
        ValueError: If neither (dx, dz) nor (dy, dz) is provided.
    """
    if dx and dz:
        alpha_x = 2 * np.arctan(dx / (2 * dz))
        alpha_y = 2 * np.arctan((ratio[1] * dx) / (2 * ratio[0] * dz))
    elif dy and dz:
        alpha_x = 2 * np.arctan((ratio[0] * dy) / (2 * ratio[1] * dz))
        alpha_y = 2 * np.arctan(dy / (2 * dz))
    else:
        raise ValueError("Either dx and dz or dy and dz must be provided.")

    return alpha_x, alpha_y


def detect_camera_resolution(camera_index=0):
    """
    Detect the active camera resolution.

    Returns:
        tuple[int, int] | tuple[None, None]:
            Width and height of the opened camera stream.
    """
    if cv2 is None:
        return None, None

    backend = cv2.CAP_DSHOW if os.name == "nt" and hasattr(cv2, "CAP_DSHOW") else cv2.CAP_ANY
    capture = cv2.VideoCapture(camera_index, backend)

    if not capture.isOpened():
        return None, None

    try:
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    finally:
        capture.release()

    if width <= 0 or height <= 0:
        return None, None

    return width, height


def apply_runtime_camera_config(config, camera_width=None, camera_height=None):
    """
    Apply runtime camera-dependent config overrides without changing the file.

    The configured video container is resized to preserve the detected camera
    aspect ratio while staying within the configured bounding box.
    """
    if not camera_width or not camera_height:
        return None

    current_width = config.get("layout.video.width")
    current_height = config.get("layout.video.height")

    if not current_width or not current_height:
        config.set("layout.video.width", camera_width)
        config.set("layout.video.height", camera_height)
        return (camera_width, camera_height)

    scale = min(current_width / camera_width, current_height / camera_height)
    fitted_width = max(1, int(round(camera_width * scale)))
    fitted_height = max(1, int(round(camera_height * scale)))

    config.set("layout.video.width", fitted_width)
    config.set("layout.video.height", fitted_height)

    return (camera_width, camera_height)


if __name__ == "__main__":
    # Example usage
    csv_file = "camera_calibration.csv"  # Replace with your actual file path
    try:
        camera_matrix, dist_coeffs, r_vecs, t_vecs = load_calibration_data(csv_file)
        print("Camera Matrix:", camera_matrix)
        print("Distortion Coefficients:", dist_coeffs)
    except FileNotFoundError:
        print(f"File {csv_file} not found.")

    # Example field of view calculation
    ratio = (4, 3)
    dx = 2.0
    dz = 5.0
    alpha_x, alpha_y = calculate_alphas(ratio=ratio, dx=dx, dz=dz)
    print(f"Alpha X: {np.degrees(alpha_x):.2f} degrees")
    print(f"Alpha Y: {np.degrees(alpha_y):.2f} degrees")
