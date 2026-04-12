from ultralytics import YOLO
import cv2
import ntinit

# Test a single image for fuel detection

# Load a model
model = YOLO("./best302.pt")  # Usign older model as it's better at its job than newer ones and isn't greyscale
inst = ntinit.getNT("testClient")
fuelTable = inst.getTable("fuelDetector")
fuelPublish = fuelTable.getStringTopic("fuelData").publish()

results = model(source="blender_test.png", stream=True, imgsz=640)  # generator of Results objects
result = next(results)
# print(result.plot())
while True:
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