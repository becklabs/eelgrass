from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import pandas as pd
import os
import datetime

def parse_exif(filename):
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

def parse_coords(exif):
    for key in ['Latitude','Longitude']:
        sign = -1 if exif.get('GPS'+key+'Ref') in ['S','W'] else 1
        numbers = exif.get('GPS'+key)
        degree = numbers[0]
        minute = numbers[1]
        second = numbers[2]
        exif[key] = sign * (int(degree) + float(minute) / 60 + float(second) / 3600)
    return exif['Latitude'], exif['Longitude']

def parse_time(exif):
    time = exif.get('GPSTimeStamp')
    date = exif.get('GPSDateStamp')
    timestr = ''
    for x in time:
        timestr += str(int(x))+' '
    ts = datetime.datetime.strptime(timestr+date,'%H %M %S %Y:%m:%d')
    return ts
    
def get(path):
    data = pd.DataFrame(columns = ['Filename','Lat','Long','Timestamp'])
    filenames = []
    latitudes = [] 
    longitudes = []
    timestamps = []
    
    for image in os.listdir(path):
        exif = parse_exif(path+image)
        lat, long = parse_coords(exif)
        ts = parse_time(exif)
        
        filenames.append(image)
        latitudes.append(lat)
        longitudes.append(long)
        timestamps.append(ts)
        
    data['Filename'] = filenames
    data['Lat'] = latitudes
    data['Long'] = longitudes
    data['Timestamp'] = timestamps
    return data
