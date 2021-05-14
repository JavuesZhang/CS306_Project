import pandas as pd
import pydeck as pdk
import numpy as np
import json
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon

data = pd.read_csv('./sample_taxi.csv').dropna()
data.drop(index=data[data['is_passenger']==0].index,inplace=True)
data['lon']=round(data['lon'],4)
data['lat']=round(data['lat'],4)
with open('./ShenzhenBorder2.txt', 'r') as f:
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
print(len(drop_indices))

data['path'] = data.apply(lambda r:[r['lon'],r['lat']],axis = 1)

data['timestamps'] = data['time'].str.slice(0,2).astype('int')*3600+data['time'].str.slice(3,5).astype('int')*60+data['time'].str.slice(6,8).astype('int')
data = data.sort_values(by = ['taxi_id','timestamps'])
data['path'] = data['path'].apply(lambda r:[r])
data['timestamps'] = data['timestamps'].apply(lambda r:[r])


df = data.groupby('taxi_id')['path','timestamps'].sum()
df = df.reset_index()
color_lookup = pdk.data_utils.assign_random_colors(df['taxi_id'])
df['color'] = df.apply(lambda row:color_lookup.get(str(row['taxi_id'])),axis=1)

df2=df.drop(columns='taxi_id')
j=df2.to_json(orient='records')
with open('./taxi.json', 'w') as f:
    f.write(j)