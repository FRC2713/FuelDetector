import time
from ultralytics import YOLO
from picamera2 import Picamera2
import ntinit

picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

# Load a model
model = YOLO("./best302.pt")  # Usign older model as it's better at its job than newer ones and isn't greyscale


inst = ntinit.getNT("detectorClient")
time.sleep(1) # Make a delay long enough to read
fuelTable = inst.getTable("fuelDetector")
fuelPublish = fuelTable.getStringTopic("fuelData").publish()

# Run inference on the source
results = model(source=0, stream=True)  # generator of Results objects

while True:
    results = model(frame)
    frame = picam2.capture_array()
    for result in results:
        # print(result.plot())
        #cv2.imshow("output", result.plot())
        boxes = result.boxes.xywh.tolist()
        confs = result.boxes.conf.tolist()
        boxString = ""
        for b in range(len(boxes)):
            boxString += str(boxes[b][0]) + "," + str(boxes[b][1]) + "," + str(boxes[b][2]) + "," + str(boxes[b][3]) + "," + str(confs[b]) + ";"
        #print(boxString)
        fuelPublish.set(boxString)
        #if cv2.pollKey() == ord('q'): # This might take a few seconds of holding down the q key to actually work; I suspect that this is because of the time spent processing the images. The diffrence between waitKey(1) and pollKey() was minimal in the result. -Owen
            #break
            #cv2.destroyAllWindows()
            #fuelPublish.close()

# model.predict("path/to/source.png", device="tpu:0") # Run on Coral