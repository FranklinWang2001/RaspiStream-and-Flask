# USAGE
# python webstreaming.py --ip 0.0.0.0 --port 8000

# import the necessary packages
from pyimagesearch.motion_detection import SingleMotionDetector
from pyimagesearch.keyclipwriter import KeyClipWriter
from imutils.video import VideoStream
from flask import Response, Flask, render_template, url_for, request
import threading
import argparse
import datetime
import imutils
import time
import cv2
import smtplib
import os
import os.path as op
import glob
from email.message import EmailMessage

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful for multiple browsers/tabs
# are viewing tthe stream)
outputFrame = None
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cf21ee8a4cee82fa62563445a4c6cdd4'

# initialize the video stream and allow the camera sensor to
# warmup
#vs = VideoStream(usePiCamera=1).start()
vs = VideoStream(src=0)

# initialize last uploaded timestamp and frame motion counter
lastUploadedEmail = datetime.datetime.now()
motionCounter = 0


@app.route("/", methods=['GET', 'POST'])
def home():
    global vs
    power = False  # if True, camera is on

    if "Camera On" in request.form:
        power = True
        vs = VideoStream(src=0).start()
        time.sleep(2.0)
    elif "Camera Off" in request.form:
        power = False
        vs.stop()

    # return the rendered template
    return render_template("home.html", power=power)


@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/saved_videos")
def saved_videos():
    video_path = ""
    if (not("/static/videos" in os.getcwd())):
        video_path = op.abspath('./static/videos')
        os.chdir(video_path)

    vid_list = glob.glob('*.mp4')
    vid_list.sort()

    return render_template("saved_videos.html", vid_list=vid_list)


def detect_motion(frameCount):
    # grab global references to the video stream, output frame, and
    # lock variables
    global vs, outputFrame, lock

    # initialize the motion detector and the total number of frames
    # read thus far
    md = SingleMotionDetector(accumWeight=0.1)
    total = 0

    # initialize KeyClipWriter, set counter for frames with no motion detected
    kcw = KeyClipWriter()
    consecFramesNoMotion = 0

    # loop over frames from the video stream
    while True:
        timestamp = datetime.datetime.now()
        text = "Unoccupied"
        # read the next frame from the video stream, resize it,
        # convert the frame to grayscale, and blur it
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)

        # if the total number of frames has reached a sufficient
        # number to construct a reasonable background model, then
        # continue to process the frame
        if total > frameCount:
            # detect motion in the image
            motion = md.detect(gray)

            # check to see if motion was found in the frame
            if motion is not None:
                # unpack the tuple and draw the box surrounding the
                # "motion area" on the output frame
                (thresh, (minX, minY, maxX, maxY)) = motion
                cv2.rectangle(frame, (minX, minY), (maxX, maxY),
                              (0, 0, 255), 2)
                text = "Occupied"

                # send email to notify user of motion
                send_email(timestamp)

                # motion has occured, so reset frames with no motion counter
                consecFramesNoMotion = 0
            else:
                consecFramesNoMotion += 1

            record_video(kcw, frame, motion, consecFramesNoMotion, timestamp)

        # grab the current timestamp and draw it on the frame
        cv2.putText(frame, timestamp.strftime(
            "%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # update the background model and increment the total number
        # of frames read thus far
        md.update(gray)
        total += 1

        # acquire the lock, set the output frame, and release the
        # lock
        with lock:
            outputFrame = frame.copy()


def generate():
    # grab global references to the output frame and lock variables
    global outputFrame, lock

    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue

            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

            # ensure the frame was successfully encoded
            if not flag:
                continue

        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
              bytearray(encodedImage) + b'\r\n')


def send_email(timestamp):
    global motionCounter, lastUploadedEmail

    min_send_seconds = 5
    min_motion_frames = 8

    # set usernames for email
    app_email = os.environ.get('APP_EMAIL')
    normal_email = os.environ.get('EMAIL_USER')
    app_pass = os.environ.get('APP_PASS')
    contacts = [app_email, normal_email]

    # prepare email message
    msg = EmailMessage()
    msg['From'] = app_email
    msg['To'] = contacts
    msg['Subject'] = 'Motion Detection Alert'
    msg.set_content('Motion detected at ' + str(timestamp))

    if (timestamp - lastUploadedEmail).seconds >= min_send_seconds:
        # increment the motion counter
        motionCounter += 1
        # check to see if the number of frames with consistent motion is
        # high enough
        if motionCounter >= min_motion_frames:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(app_email, app_pass)
                smtp.send_message(msg)

            # update the last uploaded timestamp and reset the motion
            # counter
            lastUploadedEmail = timestamp
            motionCounter = 0

    # otherwise, the room is not occupied
    else:
        motionCounter = 0


def record_video(kcw, frame, motion, consecFramesNoMotion, timestamp):
    bufferSize = 32
    outputPath = './static/videos'
    codec = 'avc1'  # record mp4 video
    fps = 20

    if motion:
        print('this code runs')
        # if we are not already recording, start recording
        if not kcw.recording:
            timeDetected = timestamp.strftime("%Y%m%d-%H%M%S")
            p = "{}/{}.mp4".format(outputPath, timeDetected)
            kcw.start(p, cv2.VideoWriter_fourcc(*codec), fps)

    # update the key frame clip buffer
    kcw.update(frame)

    # stop recording video when there are enough frames without motion
    if kcw.recording and consecFramesNoMotion >= bufferSize:
        kcw.finish()


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # construct the argument parser and parse command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, required=True,
                    help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, required=True,
                    help="ephemeral port number of the server (1024 to 65535)")
    ap.add_argument("-f", "--frame-count", type=int, default=32,
                    help="# of frames used to construct the background model")
    args = vars(ap.parse_args())

    # start a thread that will perform motion detection
    t = threading.Thread(target=detect_motion, args=(
        args["frame_count"],))
    t.daemon = True
    t.start()

    # start the flask app
    app.run(host=args["ip"], port=args["port"], debug=True,
            threaded=True, use_reloader=True)

# release the video stream pointer
vs.stop()
