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
# world record
MAX_SPEED = 120

def get_raw_data():
    print('Start loading data: '+DATA_RAW_PATH)
    data = pd.read_csv(DATA_RAW_PATH).dropna()
    # data=data[(data['is_passenger']==1)]
    # decrease the size of data
    data['lon']=round(data['lon'],6)
    data['lat']=round(data['lat'],6)
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


def drop_abnormal_speed(data, begin_hour, end_hour):

    print('Start dropping points with abnormal speed... ')
    MAX_SPEED = data.sort_values(by=['speed'], ascending=False).iloc[0, :]['speed'] / 3.6
    print('Speed limit: ' + str(MAX_SPEED))
    data['timestamps'] = data['time'].str.slice(0, 2).astype('int') * 3600 + data['time'].str.slice(3, 5).astype(
        'int') * 60 + data['time'].str.slice(6, 8).astype('int')

    data['hour'] = pd.to_datetime(data['time']).dt.hour
    data=data[(data['hour']>=begin_hour) & (data['hour']<=end_hour)]
    # save(data, './data_filtered.csv')
    # print(len(data))
    data = data.sort_values(by=['taxi_id', 'timestamps'])

    # data=pd.read_csv('./data_filtered.csv')

    taxi_id = 0
    old_lon = 0.0
    old_lat = 0.0
    old_time = 0

    drop_indices = []
    for item in data.itertuples():
        taxi_id_tmp, lon_tmp, lat_tmp, time_tmp = int(getattr(item, 'taxi_id')), float(getattr(item, 'lon')), float(
            getattr(item, 'lat')), int(getattr(item, 'timestamps'))
        if lon_tmp < -180 or lon_tmp > 180 or lat_tmp < -90 or lat_tmp > 90:
            drop_indices.append(getattr(item, 'Index'))
            continue
        if not taxi_id_tmp == taxi_id:
            taxi_id, old_lon, old_lat, old_time = taxi_id_tmp, lon_tmp, lat_tmp, time_tmp
            continue
        distance = geodesic((old_lat, old_lon), (lat_tmp, lon_tmp)).m
        if time_tmp == old_time or distance>1000 or distance / (time_tmp - old_time) > MAX_SPEED:
            drop_indices.append(getattr(item, 'Index'))
            continue
        taxi_id, old_lon, old_lat = taxi_id_tmp, lon_tmp, lat_tmp

    data.drop(drop_indices, inplace=True)
    print('Drop successfully. ')
    print(len(data))
    save(data, RESOURCE_PATH + 'after_speed.csv')
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
    # data['is_passenger'] = data['is_passenger'].apply(lambda r:[r])

    df = data.groupby('taxi_id')['path','timestamps'].sum()
    df = df.reset_index()
    color_lookup = pdk.data_utils.assign_random_colors(df['taxi_id'])
    df['color'] = df.apply(lambda row:color_lookup.get(str(row['taxi_id'])),axis=1)
    
    df2=df.drop(columns='taxi_id')
    dj=df2.to_json(orient='records')

    # color_lookup = pdk.data_utils.assign_random_colors(data['taxi_id'])
    # data['color'] = data.apply(lambda row:color_lookup.get(str(row['taxi_id'])),axis=1)

    # df2=data.drop(columns='taxi_id')
    # dj=data.to_json(orient='records')

    with open(path, 'w') as f:
        f.write(dj)
    
    print('Saved successfully to: '+path)

def process_order():
    data_OD = pd.read_csv(RESOURCE_PATH+'data_after_find_OD.csv', index_col=0)

    data = data_OD.drop(data_OD[(data_OD['is_origin']==0)&(data_OD['is_destination']==0)].index)
    data.drop(['speed', 'is_passenger'], axis=1, inplace=True)
    data['leave_time'] = ""
    data['origin_lon'] = 0.0
    data['origin_lat'] = 0.0
    data['arrive_time'] = ""
    data['destination_lon'] = 0.0
    data['destination_lat'] = 0.0
    data['will_be_drop'] = 0

    data = translate_to_order_form(data)

    data['during_time'] = (pd.to_datetime(data['arrive_time'])-pd.to_datetime(data['leave_time'])).dt.total_seconds()
    data['hour'] = (pd.to_datetime(data['leave_time'])).dt.hour
    distances=[]
    speed=[]
    for item in data.itertuples():
        origin_lon, origin_lat, destination_lon, destination_lat = \
            float(getattr(item, 'origin_lon')), \
                float(getattr(item, 'origin_lat')), \
                    float(getattr(item, 'destination_lon')), \
                        float(getattr(item, 'destination_lat'))
        distance=geodesic((origin_lat,origin_lon), (destination_lat,destination_lon)).m
        distances.append(round(distance,4))
        speed.append(int(distance/int(getattr(item, 'during_time'))*3.6))

    data['distance'] = distances
    data['speed'] = speed
    data.drop(columns=['Unnamed: 0.1'],inplace=True)
    data=data[(data['speed']<=120)]

    save(data, RESOURCE_PATH+"order.csv")

'''
Return data column:
“id","leave_time","origin_lon","origin_lat","arrive_time","destination_lon","destination_lat"
'''
def translate_to_order_form(data):
    for index, row in data.iterrows():
        if data.at[index, 'is_origin'] == 1:
            index_leave = index
            data.at[index, 'leave_time'] = data.at[index, 'time']
            data.at[index, 'origin_lon'] = data.at[index, 'lon']
            data.at[index, 'origin_lat'] = data.at[index, 'lat']

        if data.at[index, 'is_destination'] == 1:
            data.at[index_leave, 'arrive_time'] = data.at[index, 'time']
            data.at[index_leave, 'destination_lon'] = data.at[index, 'lon']
            data.at[index_leave, 'destination_lat'] = data.at[index, 'lat']
            if index != index_leave:
                data.at[index_leave, 'will_be_drop'] = 0
                data.at[index, 'will_be_drop'] = 1

    data.drop(['time', 'lon', 'lat', 'is_origin', 'is_destination'], axis=1, inplace=True)
    data.drop(data[data['will_be_drop']==1].index, inplace=True)
    data.drop(data[data['destination_lon']==0].index, inplace=True)
    data['during_time'] = pd.to_datetime(data['arrive_time'])-pd.to_datetime(data['leave_time'])
    data.drop(data[data['during_time'].dt.total_seconds()<60].index, inplace=True)
    return data.drop(['will_be_drop'], axis=1)

if __name__=='__main__':
    data=find_OD_of_data(
            add_hour_minute_path(
                drop_out_of_border(
                    drop_abnormal_speed(
                        get_raw_data(), 0, 23
                    )
                )
            )
        )

    save(data, RESOURCE_PATH+'data_processed.csv')
    save_to_json(data, RESOURCE_PATH+'data_processed_night.json')

    process_order()