from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import pandas as pd
import os
import datetime
import shutil

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
    
def get_meta(path):
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

def get_images(path):
    filenames = []
    for image in os.listdir(path):
        if image.split('.')[-1] == 'jpg':
            filenames.append(image)
    return filenames
           
def split_into_folders(data, path):
    FOLDER_NAMES = ['undefined_density','0-25','25-50','50-75','75-100',
                    'undefined_bottom','loam','sand','sandy_gravel','gravel','gravelly_cobble','cobble']
    for folder in FOLDER_NAMES:
        if folder not in os.listdir(path):
            os.mkdir(os.path.join(path, folder))
    
    for image in data:
        image_path = os.path.join(path, image)
        if 'Coverage Density' in data[image]:
            cov_dens = data[image]['Coverage Density'][-1]
            if cov_dens == 'undefined':
                shutil.copy2(image_path, os.path.join(path, 'undefined_density'))
            if cov_dens in ['0%', '25%','0%-25%']:
                print(cov_dens, image)
                shutil.copy2(image_path, os.path.join(path, '0-25'))
            if cov_dens in ['50%','25%-50%']:
                shutil.copy2(image_path, os.path.join(path, '25-50'))
            if cov_dens in ['75%','50%-75%']:
                shutil.copy2(image_path, os.path.join(path, '50-75'))
            if cov_dens in ['100%' ,'75%-100%']:
                shutil.copy2(image_path, os.path.join(path, '75-100'))
        
        if 'Bottom Type' in data[image]:
            bottom_type = data[image]['Bottom Type'][-1]
            if bottom_type == 'undefined':
                shutil.copy2(image_path, os.path.join(path, 'undefined_bottom'))
            if bottom_type == 'Loam':
                shutil.copy2(image_path, os.path.join(path, 'loam'))
            if bottom_type == 'Sand':
                shutil.copy2(image_path, os.path.join(path, 'sand'))
            if bottom_type == 'Sandy Gravel':
                shutil.copy2(image_path, os.path.join(path, 'sandy_gravel'))
            if bottom_type == 'Gravel':
                shutil.copy2(image_path, os.path.join(path, 'gravel'))
            if bottom_type == 'Gravelly Cobble':
                shutil.copy2(image_path, os.path.join(path, 'gravelly_cobble'))
            if bottom_type == 'Cobble':
                shutil.copy2(image_path, os.path.join(path, 'cobble'))

def data_to_csv(data, path):
    df = pd.DataFrame(columns=['filename','coverage_density','bottom_type'])
    i = 0
    for image in data:
        df.loc[i,'filename'] = image
        if 'Coverage Density' in data[image]:
            df['coverage_density'][i] = data[image]['Coverage Density'][-1]
        else:
            df['coverage_density'][i] = float('nan')
        if 'Bottom Type' in data[image]:
            df['bottom_type'][i] = data[image]['Bottom Type'][-1]
        else:
            df['coverage_density'][i] = float('nan')
        i+=1
    if 'annotations.csv' in os.listdir(path):
        old_df = pd.read_csv(os.path.join(path, 'annotations.csv'))
        df = pd.concat([df, old_df]).drop_duplicates().reset_index(drop=True)
    df.to_csv(os.path.join(path, 'annotations.csv'), index=False)
       