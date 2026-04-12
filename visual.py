from ultralytics import YOLO
import cv2
import ntinit

# Load a model
model = YOLO("./best302.pt")  # Usign older model as it's better at its job than newer ones and isn't greyscale
inst = ntinit.getNT("testClient")
fuelTable = inst.getTable("fuelDetector")
fuelPublish = fuelTable.getStringTopic("fuelData").publish()

results = model(source=0, stream=True, imgsz=(480, 640))  # generator of Results objects
for result in results:
    # print(result.plot())
    cv2.imshow("output", result.plot())
    boxes = result.boxes.xywh.tolist()
    confs = result.boxes.conf.tolist()
    boxString = ""
    for b in range(len(boxes)):
        boxString += str(boxes[b][0]) + "," + str(boxes[b][1]) + "," + str(boxes[b][2]) + "," + str(boxes[b][3]) + "," + str(confs[b]) + ";"
    fuelPublish.set(boxString)
    if cv2.pollKey() == ord('q'): # This might take a few seconds of holding down the q key to actually work; I suspect that this is because of the time spent processing the images. The diffrence between waitKey(1) and pollKey() was minimal in the result. -Owen
        break
cv2.destroyAllWindows()
#fuelPublish.close()

# model.predict("path/to/source.png", device="tpu:0") # Run on Coral