import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import pydeck as pdk
# import plotly as py
# from plotly.offline import iplot
# import cufflinks as cf
# import plotly.plotly as py
import plotly_express as px

DATA_PATH="../resource/data_processed.csv"
ORDER_PATH="../resource/order.csv"
state_list = ["Free", "Occupancy", "All"]
state_dict = {"Free": 0, "Occupancy": 1}
choice_list = ["State", "Order", "Speed", "Dynamic Trajectory"]
api_keys={
    'mapbox':'pk.eyJ1IjoicmphdnVlcyIsImEiOiJja29pZmh6MnAwdGl3MnZsbGF5cjhkMGZyIn0.1HOnwLeJDLcvlqnhn-BBcg'
}
ABOUT_US='''
CS306 Final Project v3.0

Group members:
@Anditty
@EdisonE3
@Gan-Cheng
@JavuesZhang


Thanks!'''

@st.cache
def load_data_by_hour(data, target_hour, state_name):
    data = data[(data['hour'] == target_hour)]
    data = data.sample(frac=0.05)

    if state_name == "Free":
        data = data[(data['is_passenger'] == 0)]
    elif state_name == "Occupancy":
        data = data[(data['is_passenger'] == 1)]

    data = data[['lat', 'lon', "speed"]]

    return data

@st.cache
def load_data(path):
    return pd.read_csv(path)

def main(df):
    st.sidebar.title("Taxi!!!!!")
    st.sidebar.header("Make your Choice!")
    choice = st.sidebar.selectbox("Analysis", choice_list)
    if choice == choice_list[0]:
        show_state(df)
    elif choice == choice_list[1]:
        show_order()
    elif choice == choice_list[2]:
        show_speed(df)
    elif choice == choice_list[3]:
        show_video()
    st.sidebar.header("About Us")
    st.sidebar.text(ABOUT_US)

@st.cache
def get_video(path):
    video_file = open(path, 'rb')
    return video_file.read()

def show_state(df):
    st.title("State Analysis")
    state_name = st.selectbox("state", state_list)

    hour_selected = st.slider("Select hour", 0, 23)

    part_df = load_data_by_hour(df, hour_selected, state_name)
    st.map(part_df)

    # data minute
    filtered = df[
        (df["hour"] == hour_selected)
    ]
    if state_name != "All":
        filtered = filtered[
            (filtered["is_passenger"] == state_dict[state_name])
        ]
    filtered = filtered.drop_duplicates(['taxi_id', 'minute'])
    hist = np.histogram(filtered["minute"], bins=60, range=(0, 60))[0]
    chart_data = pd.DataFrame({"minute": range(60), "number": hist})
    # LAYING OUT THE HISTOGRAM SECTION
    st.write("")
    st.write("**per minute between %i:00 and %i:00**" % (hour_selected, (hour_selected + 1) % 24))
    st.altair_chart(alt.Chart(chart_data).mark_area(
        interpolate='step-after',
    ).encode(
        x=alt.X("minute:Q", scale=alt.Scale(nice=False)),
        y=alt.Y("number:Q"),
        tooltip=['minute', 'number']
    ).configure_mark(
        opacity=0.5,
        color='red'
    ), use_container_width=True)

@st.cache
def get_order_data():
    return pd.read_csv(ORDER_PATH)[['origin_lon','origin_lat','destination_lon','destination_lat','hour','during_time','distance','speed']].sample(frac=0.2)

def show_order():
    df=get_order_data()
    st.title("Order Analysis")
    choice = st.selectbox("", ['Origin & Destination', 'Detail Box'])
    if choice == "Origin & Destination":
        show_order_od(df)
    elif choice == "Detail Box":
        show_order_box(df)

def show_order_od(df):
    st.header("Origin")
    hour_selected1 = st.slider("Select hour for origin", 0, 23)
    # Define a layer to display on a map
    layer = pdk.Layer(
        'HeatmapLayer',
        df[(df['hour']==hour_selected1)],                                   #数据在此输入
        get_position=['origin_lon', 'origin_lat'],               #指定经纬度的列',
        opacity=0.7,
        radiusPixels=7,
        threshold=0.08,
        intensity=5,
        colorRange=[[116,169,207],[54,144,192],[5,112,176],[3,78,123]],
    )

    # Set the viewport location
    view_state = pdk.ViewState(
        longitude=114.027465,
        latitude=22.632468,
        zoom=10,
        pitch=40,
        bearing=-10)

    # Render
    r = pdk.Deck(layers=[layer],
                initial_view_state=view_state,
                api_keys=api_keys,
                map_style='light'
                )
    st.pydeck_chart(r, True)

    st.header("Destination")
    hour_selected2 = st.slider("Select hour for destination", 0, 23)
    # Define a layer to display on a map
    layer = pdk.Layer(
        'HeatmapLayer',
        df[(df['hour']==hour_selected2)],                                   #数据在此输入
        get_position=['destination_lon', 'destination_lat'],               #指定经纬度的列',
        opacity=0.7,
        radiusPixels=7,
        threshold=0.08,
        intensity=5,
        colorRange=[[116,169,207],[54,144,192],[5,112,176],[3,78,123]],
    )

    # Set the viewport location
    view_state = pdk.ViewState(
        longitude=114.027465,
        latitude=22.632468,
        zoom=10,
        pitch=40,
        bearing=-10)

    # Render
    r = pdk.Deck(layers=[layer],
                initial_view_state=view_state,
                api_keys=api_keys,
                map_style='light'
                )
    st.pydeck_chart(r, True)

def show_order_box(df):
    st.header("Speed Box")
    fig = px.box(
        df,
        x="hour",   # 分组的数据
        y="speed",  # 箱体图的数值
        points="suspectedoutliers"
        # color="hour"  # 颜色分组
    )
    st.plotly_chart(fig)

    st.header("Distance Box")
    fig = px.box(
        df,
        x="hour",   # 分组的数据
        y="distance",  # 箱体图的数值
        points="suspectedoutliers"
        # color="hour"  # 颜色分组
    )
    st.plotly_chart(fig)

    st.header("During Time Box")
    fig = px.box(
        df,
        x="hour",   # 分组的数据
        y="during_time",  # 箱体图的数值
        points="suspectedoutliers"
        # color="hour"  # 颜色分组
    )
    st.plotly_chart(fig)

@st.cache
def speed_data(df, target_hour, target_minute):
    return df[(df['hour'] == target_hour) & (df['minute'] == target_minute)][['lon','lat','speed']].sample(frac=0.1)

@st.cache
def speed_data_for_box(df):
    return df[['hour','speed']].sample(frac=0.05)

@st.cache
def speed_data_for_jam(df, target_hour):
    return df[(df['hour'] == target_hour) & (df['speed']<10)][['lon','lat','speed']].sample(frac=0.1)

def show_speed(df):
    st.title("Speed Analysis")
    choice = st.selectbox("Choose Analysis Approach", ["None", "Map", "Box", "Traffic Jam Heatmap"])
    if choice == "Map":
        show_speed_map(df)
    elif choice == "Box":
        show_speed_box(df)
    elif choice == "Traffic Jam Heatmap":
        show_speed_jam(df)

def show_speed_map(df):
    hour_selected = st.slider("Select hour", 0, 23)
    minute_selected = st.slider("Select minute", 0, 60)
    data=speed_data(df, hour_selected, minute_selected)
    # Define a layer to display on a map
    layer = pdk.Layer(
        'HexagonLayer',
        data,                                   #数据在此输入
        get_position=['lon', 'lat'],                #指定经纬度的列
        getColorWeight = 'speed',                #指定集计数量的列
        getElevationWeight = 'speed',            #指定集计数量的列
        elevation_scale=10,
        radius = 200,                                #Hexagon的大小
        elevation_range=[0, 1000],                    #Hexagon的高低
        extruded=True,
        coverage=1
        )
    # Set the viewport location
    view_state = pdk.ViewState(
        longitude=114.027465,
        latitude=22.632468,
        zoom=10,
        pitch=25,
        bearing=-10)
    # Render
    r = pdk.Deck(layers=[layer],
                initial_view_state=view_state,
                api_keys=api_keys,
                map_style='light'
                )
    st.pydeck_chart(r)

def show_speed_box(df):
    #box chart
    df=speed_data_for_box(df)
    
    fig = px.box(
        df,
        x="hour",   # 分组的数据
        y="speed",  # 箱体图的数值
        points="suspectedoutliers"
        # color="hour"  # 颜色分组
    )
    st.plotly_chart(fig)

def show_speed_jam(df):
    hour_selected = st.slider("Select hour", 0, 23)
    data=speed_data_for_jam(df, hour_selected)
    # Define a layer to display on a map
    layer = pdk.Layer(
        'HeatmapLayer',
        data.sample(frac=0.05),                                   #数据在此输入
        get_position=['lon', 'lat'],               #指定经纬度的列',
        opacity=0.7,
        radiusPixels=7,
        threshold=0.08,
        intensity=5,
    )

    # Set the viewport location
    view_state = pdk.ViewState(
        longitude=114.027465,
        latitude=22.632468,
        zoom=10,
        pitch=40,
        bearing=-10)

    # Render
    r = pdk.Deck(layers=[layer],
                initial_view_state=view_state,
                api_keys=api_keys,
                map_style='light'
                )
    st.pydeck_chart(r, True)

def show_video():
    st.title("Dynamic Trajectory")
    choice_list=["Morning (7:00-10:00)", "Evening (18:00-21:00)"]
    choice = st.selectbox("Choose Time", choice_list)
    path=''
    if choice == choice_list[0]:
        path='../resource/Taxi_Dynamic_Trajectory_Morning.mp4'
    else:
        path='../resource/Taxi_Dynamic_Trajectory_Evening.mp4'
    video_bytes = get_video(path)
    st.video(video_bytes)

if __name__ == "__main__":
    df = load_data(DATA_PATH)
    main(df)
