import os
import os.path as op
import glob
from flask import url_for

video_path = ""
if ( not("/static/videos" in os.getcwd()) ):
    video_path = op.abspath('./static/videos')
    os.chdir(video_path)

vid_list = glob.glob('*.mp4')
vid_list.sort()

all_video_paths = []
for vid in vid_list:
    vid_abspath = op.abspath(vid)
    all_video_paths.append(vid_abspath)

combined_vid_list = []
list_size = len(vid_list)

for i in range(0, list_size):
    vid_and_abspath = (vid_list[i], all_video_paths[i])
    combined_vid_list.append(vid_and_abspath)

vid_url = url_for(vid_list[0])
print('url_for: ' + str(vid_url))
