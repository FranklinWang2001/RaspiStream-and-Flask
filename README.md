# Raspi-Streaming using Flask
A small flask server that streams video from a webcam/PiCamera.

## Requirements
To install all necessary packages: `pip install -r requirements.txt`

## Usage
From the root directory, run `python webstreaming.py --ip 0.0.0.0 --port 8000`. This will start the flask server.

Next, navigate to http://0.0.0.0:8000/ on the web browser of your choice.

![](./images/Flask-homepage.png)

You are now ready to start using the website!

Click on/off to toggle streaming:

![](./images/Camera-On.gif)

The website will automatically record any motion that it detects.

Next, navigate to the `Saved Videos` page. You can view all recorded motion here.

![](./images/saved-video.gif)
