import socket, cv2, pickle, struct
import imutils
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--camera") # argument to enable disable webcam --camera True
## make a videos folder and use them in the parser (change the deafault in the next line)
parser.add_argument("--video", default='videos/recording.mp4')  # argument --video 'videos/lcdp.mp4' --process 'type'
parser.add_argument("--process", default= 'original', choices=["edge","gesture", "original"])  # argument --process choose the type of processing to be done on the server
args = parser.parse_args()


# Getting source video from client.
wCam, hCam = 688, 480

camera = str(args.camera) # make true if you want to use the "WEB CAM"
if camera == 'enable':
    vid = cv2.VideoCapture(0)
else:
    vid = cv2.VideoCapture(str(args.video))

vid.set(3, wCam)
vid.set(4, hCam)
# end of gettin source video

# intializing the destination to the host
host = '62.114.34.87' ## don't forget to change the IP to yours(get the ip from server output)  
port = 9999
size = 1024
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect((host,port))

client_socket.send(str(args.process).encode('utf-8'))

data = client_socket.recv(size)
if len(data):
    print('Recieved:', data.decode('utf-8'))
# this will send (process type) as string in the first msg of each client connection to the server
# 'process type' is used by server threads to know the type of processing.
#  
# end initializing


if client_socket:
    while(vid.isOpened()):
        try:
            img, frame = vid.read()
            frame = imutils.resize(frame, width=380, height=250)
            a = pickle.dumps(frame)
            message = struct.pack("Q", len(a)) + a
            client_socket.sendall(message)
            
            data = b""
            payload_size  = struct.calcsize("Q")
            while True:
                # cv2.imshow(f"Recieved on Client", frame)
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
                ###
                #  image processing here
                # frame = cv2.putText(frame,text,(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
                ###
                cv2.imshow(f"Recieved on Client", frame)
                img, frame = vid.read()
                frame = imutils.resize(frame, width=380, height=250)
                a = pickle.dumps(frame)
                message = struct.pack("Q", len(a)) + a
                client_socket.sendall(message)


                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    client_socket.close()
        except:
            print('VIDEO FINISHED')
            break
