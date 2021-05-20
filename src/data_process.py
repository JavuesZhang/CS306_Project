import pandas as pd
import pydeck as pdk
import numpy as np
import json
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon
from geopy.distance import geodesic

RESOURCE_PATH='../resource/'
DATA_RAW_PATH=RESOURCE_PATH+'sample_taxi.csv'
BORDER_PATH=RESOURCE_PATH+'ShenzhenBorder.txt'

MAX_SPEED = 120

def get_raw_data():
    print('Start loading data: '+DATA_RAW_PATH)
    data = pd.read_csv(DATA_RAW_PATH).dropna()
    # decrease the size of data
    data['lon']=round(data['lon'],4)
    data['lat']=round(data['lat'],4)
    print('Data loaded successfully.')
    return data

def drop_out_of_border(data):
    print('Start dropping points out of Shenzhen City...')
    with open(BORDER_PATH, 'r') as f:
        content=[]
        for line in f.readlines():
            point = line.split(',')
            point = [float(point[0]), float(point[1])]
            content.append(point)
        border = np.array(content).reshape(-1,2)

    city = Polygon(border)
    drop_indices=[]
    for item in data.itertuples():
        if not city.contains(Point(float(getattr(item, 'lon')), float(getattr(item, 'lat')))):
            # print(getattr(item, 'Index'), float(getattr(item, 'lon')), float(getattr(item, 'lat')))
            drop_indices.append(getattr(item, 'Index'))
    data.drop(drop_indices, inplace=True)
    print('Drop successfully.')
    save(data, RESOURCE_PATH+'after_border.csv')
    return data

def drop_abnormal_speed(data):
    print('Start dropping points with abnormal speed... ')
    MAX_SPEED=data.sort_values(by=['speed'],ascending=False).iloc[0,:]['speed']/3.6
    print('Speed limit: '+str(MAX_SPEED))
    data['timestamps'] = data['time'].str.slice(0,2).astype('int')*3600+data['time'].str.slice(3,5).astype('int')*60+data['time'].str.slice(6,8).astype('int')
    data = data.sort_values(by = ['taxi_id','timestamps'])

    taxi_id=0
    old_lon=0.0
    old_lat=0.0

    drop_indices=[]
    for item in data.itertuples():
        taxi_id_tmp, lon_tmp, lat_tmp = int(getattr(item, 'taxi_id')), float(getattr(item, 'lon')), float(getattr(item, 'lat'))
        if lon_tmp < -180 or lon_tmp > 180 or lat_tmp < -90 or lat_tmp > 90:
            drop_indices.append(getattr(item, 'Index'))
            continue
        if not taxi_id_tmp == taxi_id:
            taxi_id, old_lon, old_lat = taxi_id_tmp, lon_tmp, lat_tmp
            continue
        time = getattr(item, 'timestamps')
        if geodesic((old_lat,old_lon), (lat_tmp,lon_tmp)).m/time > MAX_SPEED:
            drop_indices.append(getattr(item, 'Index'))
            continue
        taxi_id, old_lon, old_lat = taxi_id_tmp, lon_tmp, lat_tmp
        
    data.drop(drop_indices, inplace=True)
    print('Drop successfully. ')
    save(data, RESOURCE_PATH+'after_speed.csv')
    return data

def add_hour_minute_path(data):
    print('Start adding columns: hour, minute, path...')
    data['hour'] = data['time'].str.slice(0,2).astype('int')
    data['minute'] = data['time'].str.slice(3,5).astype('int')
    data['path'] = data.apply(lambda r:[r['lon'],r['lat']],axis = 1)
    print('Add successfully. ')
    save(data, RESOURCE_PATH+'after_add.csv')
    
    return data

def find_OD_of_data(data_OD):
    print('Start finding origin and destination:...')
    data_OD['is_origin'] = 0
    data_OD['is_destination'] = 0
    index_pre = data_OD.index[0]
    for index, row in data_OD.iterrows():
        if index is not index_pre:
            if data_OD.at[index_pre, 'taxi_id'] == row['taxi_id']:
                if data_OD.at[index_pre, 'is_passenger'] and not row['is_passenger']:
                    data_OD.at[index_pre, 'is_destination'] = 1
                elif not data_OD.at[index_pre, 'is_passenger'] and row['is_passenger']:
                    data_OD.at[index, 'is_origin'] = 1
        index_pre = index
    
    print('Find successfully.')
    return data_OD


def save(data, path):
    print('Saving to: '+path)
    data.to_csv(path, index=False) 
    print('Saved successfully to: '+path)

def save_to_json(data, path):
    print('Saving to: '+path)
    data['path'] = data['path'].apply(lambda r:[r])
    data['timestamps'] = data['timestamps'].apply(lambda r:[r])
    data['is_passenger'] = data['is_passenger'].apply(lambda r:[r])

    df = data.groupby('taxi_id')['path','timestamps','is_passenger'].sum()
    df = df.reset_index()
    color_lookup = pdk.data_utils.assign_random_colors(df['taxi_id'])
    df['color'] = df.apply(lambda row:color_lookup.get(str(row['taxi_id'])),axis=1)

    df2=df.drop(columns='taxi_id')
    dj=df2.to_json(orient='records')
    with open(path, 'w') as f:
        f.write(dj)
    
    print('Saved successfully to: '+path)

if __name__=='__main__':
    # data=find_OD_of_data(
    #         add_hour_minute_path(
    #             drop_out_of_border(
    #                 drop_abnormal_speed(
    #                     get_raw_data()
    #                 )
    #             )
    #         )
    #     )
    data=find_OD_of_data(
            add_hour_minute_path(
                drop_out_of_border(
                    pd.read_csv('../resource/after_speed.csv')
                )
            )
        )
    save(data, RESOURCE_PATH+'data_processed.csv')
    save_to_json(data, RESOURCE_PATH+'data_processed.json')