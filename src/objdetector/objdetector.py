from argparse import Namespace
from pathlib import PosixPath
from notebooks.yolov5.detect import run



class ObjDetector:
    ''' Interface to custom trained YOLOv5 Object detection model. '''
    def __init__(self, img_path = "test.png", weights=['notebooks/yolov5/runs/train/exp007/weights/best_309.pt']):
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
            hide_conf=False,
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
            source=f'{img_path}',
            update=False,
            vid_stride=1,
            view_img=False,
            visualize=False,
            weights=weights)

    def detect(self):
        '''
            Returns a collections.defaultdict(list) with possible keys, if detected,
            correspodning to the labels: utils.utils.IMAGE_LABELS
                LOGIN = 'Login Field'
                PASSWORD = 'Password Field'
                CONTINUE = 'Continue'
                GOOGLE_AUTH = 'Google Auth'

            Each value is a list containing a list [p1,p2,conf]
            For example, if 3 objects are detected in an image, each object gets:
            p1 = top left corner (x1, y1)
            p2 = bottom right corner (x2, y2)
            conf = confidence from model, represents accuracy of detection for the key/label
            So, if a continue button is detected, a [p1,p2,conf] is appened to that key's list.

            res = {
                LOGIN: [[p1,p2,conf], ...],
                CONTINUE: [[p1,p2,conf], [p1,p2,conf], ...],
                ...,
            }

            No keys in the dict means that no objects were detected.

        '''

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
        except FileNotFoundError as err:
            print("No image to test! ", err)
            return None
        except Exception as error:
            print("Obj detect err: ", error)
            return None
