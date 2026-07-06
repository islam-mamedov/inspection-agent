from ultralytics import YOLO
import sys

model = YOLO("models/YOLOv8s_v24.pt")
results = model(sys.argv[1])

for r in results:
    if len(r.boxes) == 0:
        print("No defects detected.")
    for box in r.boxes:
        cls_name = model.names[int(box.cls)]
        conf = float(box.conf)
        print(f"{cls_name}: {conf:.2f} at {[round(x) for x in box.xyxy[0].tolist()]}")