import cv2


#load the camera
print("--------------------------------Loading the camera--------------------------------")
cap = cv2.VideoCapture(0)
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Can not open the camera")
        break

    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord("e"):
        print("exit")
        break

cap.release()
cv2.destroyAllWindows()

