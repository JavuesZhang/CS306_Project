import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import pydeck as pdk


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


def relation_time_number():
    st.title("relation between taxi number and time")
    df = pd.read_csv("sample_taxi_modified.csv")

    sub_df = df[['hour', 'taxi_id']]
    sub_df = sub_df.drop_duplicates()
    sub_df = sub_df.groupby(['hour']).count()

    st.line_chart(sub_df["taxi_id"])


def map_taxi():
    df = pd.read_csv("sample_taxi_modified.csv")
    # df['hour'] = pd.to_datetime(df['time']).dt.hour
    # df['minute'] = pd.to_datetime(df['time']).dt.minute

    state_list = ["Free", "Occupancy", "All"]
    state_dict = {"Free": 0, "Occupancy": 1}
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

    # clf_k_means = KMeans(n_clusters=1000, max_iter=10)
    # print("clf_KMeans聚类中心\n", clf_k_means.cluster_centers_)

    # st.pydeck_chart(pdk.Deck(
    #     map_style='mapbox://styles/mapbox/light-v9',
    #     initial_view_state=pdk.ViewState(
    #         latitude=22.7,
    #         longitude=114.0,
    #         zoom=10,
    #         pitch=50,
    #     ),
    #     layers=[
    #         pdk.Layer(
    #             'HexagonLayer',
    #             data=part_df,
    #             get_position='[lon, lat]',
    #             radius=200,
    #             elevation_scale=4,
    #             elevation_range=[0, 1000],
    #             pickable=True,
    #             extruded=True,
    #         ),
    #         pdk.Layer(
    #             'ScatterplotLayer',
    #             data=part_df,
    #             get_position='[lon, lat]',
    #             get_color='[200, 30, 0, 160]',
    #             get_radius=200,
    #         ),
    #     ],
    # ))


if __name__ == "__main__":
    map_taxi()
