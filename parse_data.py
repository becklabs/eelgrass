import re
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import pandas as pd
import os
import dateparser

def get_exif(filename):
    exif = Image.open(filename)._getexif()

    if exif is not None:
        exifkeys = [x for x in exif.keys()]
        for key in exifkeys:
            name = TAGS.get(key,key)
            exif[name] = exif.pop(key)
            
        if 'GPSInfo' in exif:
            exifkeys2 = [x for x in exif['GPSInfo'].keys()]
            for key in exifkeys2:
                name = GPSTAGS.get(key,key)
                exif['GPSInfo'][name] = exif['GPSInfo'].pop(key)

    return exif['GPSInfo']

def parse_coords(info):
    for key in ['Latitude','Longitude']:
        sign = -1 if info.get('GPS'+key+'Ref') in ['S','W'] else 1
        numbers = info.get('GPS'+key)
        degree = numbers[0]
        minute = numbers[1]
        second = numbers[2]
        info[key] = sign * (int(degree) + float(minute) / 60 + float(second) / 3600)
    return info['Latitude'], info['Longitude']

def parse_ts(info):
    time = info.get('GPSTimeStamp')
    date = info.get('GPSDateStamp')
    timestr = ''
    for x in time[:2]:
        str1 = str(x) +':'
        timestr += str1
    timestr += str(time[3])
    ts = dateparser.parse(date+' '+timestr)
    return ts
    
def get_images(path):
    data = pd.DataFrame(columns = ['Filename','Lat','Long','Timestamp','CD','BT'])
    filenames = []
    latitudes = [] 
    longitudes = []
    timestamps = []
    for image in os.listdir(path):
        exif = get_exif(path+image)
        lat, long = parse_coords(exif)
        ts = parse_ts(exif)
        filenames.append(image)
        latitudes.append(lat)
        longitudes.append(long)
        timestamps.append(ts)
    data['Filename'] = filenames
    data['Lat'] = latitudes
    data['Long'] = longitudes
    data['Timestamp'] = timestamps
    return data
