import os
import acoular as ac
from pathlib import Path
from bokeh.plotting import curdoc
from ui import Dashboard
from data_processing import Processor 
import argparse

from config import * 


ac.config.global_caching = "none"

CONFIG_PATH = "config/config.json"
config = ConfigManager(CONFIG_PATH)

camera_width = os.environ.get("ACOUSTIC_CAMERA_CAMERA_WIDTH")
camera_height = os.environ.get("ACOUSTIC_CAMERA_CAMERA_HEIGHT")
camera_ratio = apply_runtime_camera_config(
    config,
    int(camera_width) if camera_width else None,
    int(camera_height) if camera_height else None,
)

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, help="Path to an explicit checkpoint (.keras)")
args, unknown = parser.parse_known_args()


def get_default_model_directory():
    base_directory = str(config.get("model.base_directory", "models")).strip("/")
    model_name = config.get("model.name")
    return Path(base_directory) / model_name


def resolve_checkpoint_path(model_argument):
    file_pattern = config.get("model.checkpoint.file_pattern")

    if model_argument:
        candidate_path = Path(model_argument).expanduser()
        if candidate_path.is_file():
            return candidate_path
        if candidate_path.suffix:
            raise FileNotFoundError(f"Checkpoint file not found: '{candidate_path}'.")
        ckpt_directory = candidate_path / config.get("model.checkpoint.directory")
    else:
        ckpt_directory = get_default_model_directory() / config.get("model.checkpoint.directory")

    ckpt_files = sorted(
        ckpt_directory.glob(file_pattern),
        key=lambda path: int(path.stem.split("-")[0]),
    )

    if not ckpt_files:
        raise FileNotFoundError(
            f"No checkpoint files matching '{file_pattern}' were found in '{ckpt_directory}'."
        )

    return ckpt_files[-1]


model_on = True

try:
    ckpt_path = resolve_checkpoint_path(args.model)
except FileNotFoundError as exc:
    if args.model:
        raise
    print(f"Warning: {exc} Starting without the deep learning model.")
    ckpt_path = None
    model_on = False

results_folder = 'results'

# check if folder exists
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

video_index = 0
#from.helpers import list_cameras
#video_index = list_cameras()[0] # get the first valid camera index

device_index = get_uma16_index() # type: ignore
if device_index == None:
    device_index = 0


alphas = calculate_alphas(
    ratio=camera_ratio or (4, 3),
    dx=config.get("app_settings.dx"),
    dz=config.get("app_settings.dz"),
) # type: ignore

base_path = config.get("acoular.micgeom_file.base_path")
file_name = config.get("acoular.micgeom_file.file_name")

micgeom_path = Path(ac.__file__).parent / base_path / file_name
    
processor = Processor(
    config,
    device_index,
    micgeom_path,
    results_folder,
    ckpt_path,
    model_on,
    config.get("app_default_settings.z"))

dashboard = Dashboard(
    config,
    processor,
    model_on,
    alphas)


doc = curdoc()
doc.add_root(dashboard.get_layout())
