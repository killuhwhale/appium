from argparse import Namespace
from pathlib import PosixPath
from notebooks.yolov5.detect import run



class ObjDetector:
    def __init__(self, img_name = "test.png", weights=['notebooks/yolov5/runs/train/exp11/weights/best.pt']):
        self.opt = Namespace(
            agnostic_nms=False,
            augment=False, 
            classes=None, 
            conf_thres=0.2, 
            data=PosixPath('notebooks/yolov5/data/coco128.yaml'), 
            device='', 
            dnn=False, 
            exist_ok=False, 
            half=False, 
            hide_conf=True, 
            hide_labels=False, 
            imgsz=[640, 640], 
            iou_thres=0.45, 
            line_thickness=3, 
            max_det=1000, 
            name='exp', 
            nosave=False, 
            project=PosixPath('notebooks/yolov5/runs/detect'), 
            save_conf=False, 
            save_crop=False, 
            save_txt=False, 
            source=f'notebooks/yolo_images/{img_name}', 
            update=False, 
            vid_stride=1, 
            view_img=False, 
            visualize=False, 
            weights=weights)
    
    def detect(self):
        res=  None
        try:
            res = run(**vars(self.opt))
            # print("Results from ObjDetector: ", res)
            # for k,v in res.items():
            #     print(f"Here are all the {k} areas")
            #     # Sorted by confidence
            #     for area_info in sorted(v, key = lambda p: p[2], reverse=True):
            #         print(f"Click somewhere in between {area_info[0]}, {area_info[1]} w/ {area_info[2]} conf that it is a {k} label")
            return res
        except FileNotFoundError as e:
            print("No image to test! ")
            return None
        