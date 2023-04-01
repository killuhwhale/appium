from collections import defaultdict
from local_ultralytics import YOLO
from utils.app_utils import get_root_path
from utils.utils import CONFIG


class YoloV8:
    ''' Simple class to wrap ultralytics to detect.'''

    def __init__(self, weights: str, src: str):
        self.__source_img = src
        self.__model = YOLO(weights)
        self.options = {
            'save': CONFIG.save_yolov8_predicts,
            'save_conf': CONFIG.save_yolov8_predicts,
            'verbose': False,
        }

    def detect(self):
        result = defaultdict(list)
        _res = self.__model(source=self.__source_img, **self.options)
        '''
            Returns a dict of results.

        '''
        labels = _res[0].names
        boxes = _res[0].boxes.xyxy.tolist()
        confs = _res[0].boxes.conf.tolist()
        detected_labels = _res[0].boxes.cls.tolist()
        for box,  conf, label_num in zip(boxes, confs, detected_labels):
            label = labels[label_num]
            # print(f"Found {label} @ {box=} w/ conf: {conf=}")
            p1, p2 = (int(box[0]), int(box[1])), (int(box[2]), int(box[3]))
            result[label].append((p1, p2, conf, ))
        return result


class YoloV8_train:
    ''' Simple class to wrap ultralytics to train.
        Run this file directly,  python3 objdetector/yolov8.py
    '''

    def __init__(self):
        # self.__training_model = YOLO('yolov8n.pt')
        self.__training_model = YOLO('yolov8m.pt')
        self.__data = f"{get_root_path()}/coco128.yaml"

    def train(self):
        results = self.__training_model.train(data=self.__data, epochs=75)

if __name__ == "__main__":
    print(get_root_path())
    yolo = YoloV8_train()
    yolo.train()