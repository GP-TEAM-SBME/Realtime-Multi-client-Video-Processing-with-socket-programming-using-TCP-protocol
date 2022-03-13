import cv2
import mediapipe as mp
import time


class handDetector():
    '''
    The class for the gesture detection and tracking.
    '''
    def __init__(self, mode=False, modelComplexity=1, maxHands=2, detectionCon=0.5, trackCon=0.5):
        '''
        The init function required for class instantiation.

        :param mode: (boolean, default=False) used to process video.
        :param modelComplexity: (int, default=1) the complexity of the detector.
        :param maxHands: (int, default=2) max number of hands that can appear.
        :param detectionCon: (float, default=0.5) confidence threshold of detection.
        :param trackCon: (float, default=0.5) confidence threshold of tracking.
        '''

        self.mode = mode
        self.modelComplexity = modelComplexity
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        # Creating an object of hand tracking detector from mediapipe module
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.modelComplexity,
                                        self.detectionCon, self.trackCon)
        # Create an object for drawing connections between different landmarks of the hand
        self.mpDraw = mp.solutions.drawing_utils

    def findHands(self, img, draw=True):
        '''
        Detect hands within a frame with the option to draw connections between different landmarks

        :param img: (array) the frame passed to detect hands within it.
        :param draw: (boolean, default=True) drawing landmarks with small circles and connection lines between them.
        :return:
        img: (array) the return frame with hands detected (if any) and the connections between different landmarks (if draw=True)
        '''

        # Convert the frame to be in RGB format
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Pass the frame to the hand detector
        self.results = self.hands.process(imgRGB)

        # check if any hand was detected in the frame
        if self.results.multi_hand_landmarks:
            # draw circles on each landmark and connection lines between them for the detected hand(s)
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS)
        #return back the frame after detection and drawing
        return img

    def findPosition(self, img, handNo=0, draw=True):
        '''
        Return the coordinates for the detected hand landmarks

        :param img: (array) the frame passed get landmarks coordinates from.
        :param handNo: (int, default=0) the id of the hand either 0 for the first (right) hand detected nor 1 for the second.
        :param draw: (boolean, default=True) drawing a big circle on every landmark detected within the frame.
        :return:
        lmList: (list): list containing the id for every landmark detected and its coordinates with respect to the frame.
        '''
        # Create empty list for to append every landmark detected within the selected hand
        lmList = []

        # check if any hand was detected in the frame
        if self.results.multi_hand_landmarks:
            # get the landmarks for the desired hand
            myHand = self.results.multi_hand_landmarks[handNo]
            # Iterate over different landmark detected in the desired hand.
            for id, lm in enumerate(myHand.landmark):
                # get the shape of the frame
                h, w, c = img.shape
                # get the center of the landmark, since lm.x is normalized by the width of the frame so we need
                # to multiply it back by the width of the frame, similarly with lm.y ,
                cx, cy = int(lm.x * w), int(lm.y * h)
                # append the id of the landmark and its center.
                lmList.append([id, cx, cy])
                # if True draw big circles on each landmark detected
                if draw:
                    cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

        return lmList


def main():
    # Test code
    pTime = 0
    cTime = 0
    # Get the vid from camera
    cap = cv2.VideoCapture(1)
    # Create the detector
    detector = handDetector()


    while True:
        # Get the frame form camera
        success, img = cap.read()
        # pass the frame to the detector to get the back a frame with the hand(s) detected if any where found
        img = detector.findHands(img)
        # Get the coordinates for different landmarks detected
        lmList = detector.findPosition(img)
        # if len(lmList) != 0:
        #     print(lmList4])

        # Calculate fps
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        # show the fps rate at the top left corner of the live camera
        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3,
                    (255, 0, 255), 3)

        # Show the camera now and put a small delay.
        cv2.imshow("Image", img)
        cv2.waitKey(1)

# Execute main (test code) if this script is running.
if __name__ == "__main__":
    main()