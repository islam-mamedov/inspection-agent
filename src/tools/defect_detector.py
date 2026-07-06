from ultralytics import YOLO
import os

MODEL_PATH = "models/YOLOv8s_v24.pt"
CONF_THRESHOLD = 0.4

_model = None  # lazy singleton - load once, reuse


def _get_model():
    global _model
    if _model is None:
        _model = YOLO(MODEL_PATH)
    return _model


def severity_heuristic(cls_name: str, conf: float, bbox: list, img_w: int, img_h: int) -> str:
    """Rough severity from relative defect size. Documented limitation:
    a real system would use calibrated measurements."""
    x1, y1, x2, y2 = bbox
    area_frac = ((x2 - x1) * (y2 - y1)) / (img_w * img_h)
    if area_frac > 0.25:
        return "high"
    if area_frac > 0.08:
        return "medium"
    return "low"


def detect_defects(image_path: str) -> dict:
    """Run the trained detector. Returns structured findings for the agent."""
    if not os.path.exists(image_path):
        return {
            "image": image_path,
            "defects_found": 0,
            "findings": [],
            "error": f"Image file not found: {image_path}",
            "model": "YOLOv8s (fine-tuned, 1770-image structural defect dataset)",
        }

    model = _get_model()
    results = model(image_path, conf=CONF_THRESHOLD, verbose=False)
    r = results[0]
    img_h, img_w = r.orig_shape

    findings = []
    for box in r.boxes:
        cls_name = model.names[int(box.cls)]
        conf = round(float(box.conf), 2)
        bbox = [round(x) for x in box.xyxy[0].tolist()]
        findings.append({
            "defect_type": cls_name,
            "confidence": conf,
            "bbox": bbox,
            "severity": severity_heuristic(cls_name, conf, bbox, img_w, img_h),
        })

    return {
        "image": image_path,
        "defects_found": len(findings),
        "findings": findings,
        "model": "YOLOv8s (fine-tuned, 1770-image structural defect dataset)",
    }