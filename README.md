# CS306 Project Taxi Data Visualization
> Members:  
> 11812106 马永煜; 11812206 詹子正; 11812424 黄浩洋; 11812425 张佳雨

## Usage
### Get data
**1. Use demo data**  
Unzip `resource.7z` and `order.7z` in `resource/`  

**2. Use your own data**  
- Put your own `sample_taxi.csv` in `resource/`  
    ```
    "sample_taxi.csv" format:

        taxi_id,time,lon,lat,is_passenger,speed
        22224,10:13:42,113.887032,22.547518,0,0
        ...
    ```
- `cd src`
- Process data with `data_process.py`
    ```bash
    python data_process.py
    ```
    Then you will get some data files in `resource/`.

You will get `data_processed.csv`, `data_processed.json` and `order.csv`.
### Static Analysis
```bash
cd ../src
streamlit run streamlitDemo.py
```
### Dynamic Trajectory
```bash
cd ..
npm install
npm start
```