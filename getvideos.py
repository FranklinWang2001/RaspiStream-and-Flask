import os
import glob

index = 0
os.chdir('/Users/Alt/Desktop/projects/RaspiStream-and-Flask/static/videos')
vid_list = glob.glob('*.avi')
vid_list.sort()
print(vid_list)
# for file in glob.glob('*.avi'):
    # vid_list.append(file)
