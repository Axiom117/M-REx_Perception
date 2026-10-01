from ultralytics import YOLO
import pandas as pd
import sys
import torch
from pathlib import Path
from PIL import Image

# Resolve file locations relative to this script so the code is portable
SCRIPT_DIR = Path(__file__).resolve().parent


def get_model_path():
    # Prefer the trained embryo model; fall back to the bundled pretrained model
    model_path = SCRIPT_DIR / "models" / "best.pt"
    if model_path.exists():
        return model_path

    fallback_path = SCRIPT_DIR / "models" / "yolov8n-obb.pt"
    print(f"WARNING: trained model not found at {model_path}; using {fallback_path} instead.")
    print("Copy the trained best.pt from the Windows machine into python/models/ for embryo detections.")
    return fallback_path


def get_device():
    if torch.cuda.is_available():
        return 0
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def predict_single_image(image_path, output_csv="obb_predictions_v3.csv"):
    model = YOLO(str(get_model_path()))

    image = Image.open(image_path)
    image_width, image_height = image.size
    print(f"Image size: {image_width}x{image_height}")

    results = model.predict(
        source=image_path,  
        imgsz=640,
        conf=0.8,
        device=get_device(),
        save=True,
        show_labels=False,
        show_conf=False,
    )

    rows = []
    for result in results:
        image_name = Path(result.path).name

        if result.obb is None or len(result.obb) == 0:
            continue

        # xyz and angle
        obb_data = result.obb.xywhr.cpu().numpy()
        classes = result.obb.cls.cpu().numpy()
        confidences = result.obb.conf.cpu().numpy()

        for box, cls, conf in zip(obb_data, classes, confidences):
            x_center, y_center, width, height, angle = box

            rows.append({
                "image": image_name,
                "image_width": image_width,
                "image_height": image_height,
                "class_id": int(cls),
                 "confidence": float(conf),
                "x": float(x_center),
                "y": float(y_center),
                "width": float(width),
                "height": float(height),
                "theta": float(angle),
            })

    columns = ["image", "image_width", "image_height", "class_id",
               "confidence", "x", "y", "width", "height", "theta"]
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(output_csv, index=False)

    print(f"Saved {len(df)} detections from {image_path} to {output_csv}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Please provide the path to the image as a command line argument.")
    image_path = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "obb_predictions_v3.csv"

    predict_single_image(
        image_path=image_path,
        output_csv=output_csv,
    )
