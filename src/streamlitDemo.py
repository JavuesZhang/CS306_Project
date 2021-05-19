import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import pydeck as pdk

DATA_PATH="../resource/data_processed.csv"
state_list = ["Free", "Occupancy", "All"]
state_dict = {"Free": 0, "Occupancy": 1}
choice_list = ["State", "Origin&Destination", "Speed"]
api_keys={
    'mapbox':'pk.eyJ1IjoicmphdnVlcyIsImEiOiJja29pZmh6MnAwdGl3MnZsbGF5cjhkMGZyIn0.1HOnwLeJDLcvlqnhn-BBcg'
}

@st.cache
def load_data_by_hour(data, target_hour, state_name):
    data = data[(data['hour'] == target_hour)]
    data = data.sample(frac=0.05)

    if state_name == "Free":
        data = data[(data['is_passenger'] == 0)]
    elif state_name == "Occupancy":
        data = data[(data['is_passenger'] == 1)]

    data = data[['lat', 'lon']]

    return data

@st.cache
def load_data(path):
    return pd.read_csv(path)

def relation_time_number():
    st.title("relation between taxi number and time")
    df = pd.read_csv(DATA_PATH)

    sub_df = df[['hour', 'taxi_id']]
    sub_df = sub_df.drop_duplicates()
    sub_df = sub_df.groupby(['hour']).count()

    st.line_chart(sub_df["taxi_id"])


def main(df):
    choice = st.sidebar.selectbox("Analysis", choice_list)
    if choice == choice_list[0]:
        show_state(df)
    elif choice == choice_list[1]:
        show_od(df)
    else:
        show_speed(df)

def show_state(df):
    state_name = st.sidebar.selectbox("state", state_list)

    hour_selected = st.slider("Select hour of pickup", 0, 23)

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
    chart_data = pd.DataFrame({"minute": range(60), "pickups": hist})
    # LAYING OUT THE HISTOGRAM SECTION
    st.write("")
    st.write("**per minute between %i:00 and %i:00**" % (hour_selected, (hour_selected + 1) % 24))
    st.altair_chart(alt.Chart(chart_data).mark_area(
        interpolate='step-after',
    ).encode(
        x=alt.X("minute:Q", scale=alt.Scale(nice=False)),
        y=alt.Y("pickups:Q"),
        tooltip=['minute', 'pickups']
    ).configure_mark(
        opacity=0.5,
        color='red'
    ), use_container_width=True)

def show_od(df):
    choice = st.sidebar.radio('', ('Origin', 'Destination'))
    if choice == 'Origin':
        filtered=df[
            (df['is_origin']==1)
        ]
    else:
        filtered=df[
            (df['is_destination']==1)
        ]
    # Define a layer to display on a map
    layer = pdk.Layer(
        'HeatmapLayer',
        filtered.sample(frac=0.05),                                   #数据在此输入
        get_position=['lon', 'lat'],               #指定经纬度的列',
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

@st.cache
def speed_data(df):
    return df[['lon','lat','speed']].sample(frac=0.01)


def show_speed(df):
    data=speed_data(df)
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

if __name__ == "__main__":
    df = load_data(DATA_PATH)
    main(df)
