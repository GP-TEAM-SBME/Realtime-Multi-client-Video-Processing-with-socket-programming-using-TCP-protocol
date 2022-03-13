import socket, cv2, pickle, struct
import threading
import numpy as np
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import HandTrackingModule as htm

# initializing server 
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print('HOST IP: ', host_ip)
port = 9999
server_address = (host_ip, port)

print('starting on %s port %s' % server_address)
sock.bind(server_address)
sock.listen()
print("Listening at: ", server_address)
# end of server initialization 


# initialize the Detector and the necessary variables
# Create a hand detector with higher detection confidence than the tracking confidence
detector = htm.handDetector(detectionCon=0.7)

# Get the speakers used by the laptop
devices = AudioUtilities.GetSpeakers()
# Allowing to access the speaker and change its volume for our code
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

# GEt the range for the volume
volRange = volume.GetVolumeRange()
minVol = volRange[0]
maxVol = volRange[1]
vol = 0
volBar = 400
volPer = 0
# end of initializing hand gesture detector


def show_client(addr, client_socket):
    '''
    This function is used by the threads on the server to perform the 
    image processing and send the processed frames back to the client.
    '''
    if client_socket:
        # getting the first msg from client (processing type)
        data = client_socket.recv(1024)
        data_decoded = data.decode("utf-8")
        data = f"Processing {data_decoded} on server"
        client_socket.sendall(data.encode("UTF-8"))
        # send msg back to client

        # start accepting frames from client
        data = b""
        payload_size  = struct.calcsize("Q")
        try:         
            while True:
                # reconstructing the frame from client packets
                while len(data) < payload_size:
                    packet = client_socket.recv(4*1024)
                    if not packet: break
                    data += packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]
                while len(data) < msg_size:
                    data += client_socket.recv(4*1024)
                frame_data = data[:msg_size]
                data = data[msg_size:]
                frame = pickle.loads(frame_data)
                #end of frame reconstruction
                text = f"CLIENT: {addr}"
                

                # cv2.imshow(f"Recieved on Server", frame)

                # image processing here
                
                if data_decoded == 'edge':
                    # more on edge detection : https://en.wikipedia.org/wiki/Canny_edge_detector
                    edges = cv2.Canny(frame,100,200)  ## cany edge detection 
                    frame = cv2.putText(edges,'edge procesing',(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
                elif data_decoded == 'original':
                    frame = cv2.putText(frame,'original stream',(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
                elif data_decoded == 'gesture':
                    # Pass the frame to the detector and get the frame back containing the detected hands (if any)
                    frame = detector.findHands(frame)
                    # Get the landmarks coordinates of the detected hand
                    lmList = detector.findPosition(frame, draw=False)
                    # Check that there is a detected hand
                    if len(lmList) != 0:
                        # Get the coordinates for the thumb (id=4) and pointer finger (id=8)
                        x1, y1 = lmList[4][1], lmList[4][2]
                        x2, y2 = lmList[8][1], lmList[8][2]
                        # Calculate the center between the two landmarks
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                        # Draw a big pink circle on the thumb and the pointer fingers, aline between them and a circle
                        # on the center point between them
                        cv2.circle(frame, (x1, y1), 5, (255, 0, 255), cv2.FILLED)
                        cv2.circle(frame, (x2, y2), 5, (255, 0, 255), cv2.FILLED)
                        cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
                        # Calculate the distance between thumb and pointer finger
                        length = math.hypot(x2 - x1, y2 - y1)
                        # Interpolate the length range to the volume range
                        vol = np.interp(length, [15, 300], [minVol, maxVol])
                        # Interpolate the length range to the volume Bar range
                        volBar = np.interp(length, [20, 100], [400, 150])
                        # Interpolate the length range to the volume percentage range that appear under the bar.
                        volPer = np.interp(length, [20, 100], [0, 100])
                        # Set the volume based on the interpolated vol based on the length between thumb and point finger
                        volume.SetMasterVolumeLevel(vol, None)

                        # If the length != 0 make the center circle blue
                        if length:
                            cv2.circle(frame, (cx, cy), 5, (0, 255, 0), cv2.FILLED)
                    frame = cv2.putText(frame,'hand gesture detection',(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
            
                
                # end of image processing

                # resend the processed frame tothe corresponding client 
                a = pickle.dumps(frame)
                message = struct.pack("Q", len(a)) + a 
                client_socket.sendall(message)           
        finally:
            client_socket.close() 

while True:
    client_socket, addr = sock.accept()
    thread = threading.Thread(target=show_client, args=(addr,client_socket))
    thread.start()  # create thread to handle each client request 
    print("TOTAL CLIENTS: ", threading.active_count() - 1)



