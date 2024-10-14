# CS506_Final_Project
### **Project: Predicting Wave Heights Based on Wind Speed and Atmospheric Pressure**

#### **Goal**:
The goal is to build a predictive model for wave heights based on wind speed, atmospheric pressure, and other relevant weather conditions. This can be valuable for maritime safety, surfing conditions, or coastal erosion management.

#### **Data Collection**:
- **Wave Height Data**: Collect historical wave height data from buoys deployed by organizations such as [NOAA's National Data Buoy Center (NDBC)](https://www.ndbc.noaa.gov/) which provides real-time and historical wave measurements across the world’s oceans.
- **Wind Speed and Atmospheric Pressure Data**: Gather historical weather data (wind speed, atmospheric pressure, and temperature) from the [OpenWeather API](https://openweathermap.org/api) or directly from NOAA’s [Weather and Oceanographic Data Center](https://www.noaa.gov/).
- **Sea Surface Temperature Data**: Include sea surface temperature from sources like NASA’s [Ocean Color Data](https://oceancolor.gsfc.nasa.gov/).

#### **Modeling**:
- **Baseline Model**: Start with linear regression using wind speed and pressure as features to predict wave height.
- **Advanced Model**: Implement machine learning models like Random Forest or XGBoost to capture more complex relationships between wind, pressure, and wave heights. 
- **Time-Series Forecasting**: Use models like ARIMA or LSTM to forecast wave heights over time based on historical patterns.

#### **Data Visualization**:
- **Wave Height Over Time**: Create time-series plots to visualize wave height fluctuations across different seasons and weather events.
- **Wind Speed vs Wave Height**: Generate scatter plots or interactive 3D plots showing the correlation between wind speed and wave height.
- **Geographic Heat Maps**: Show the areas where wave heights are most affected by wind speed, using a geographic heat map.

#### **Test Plan**:
- Use a **train/test split** The data choose from 2019 to 2024( 80% of the data for training, 20% for testing from ) to evaluate the performance of your predictive models.

Adressing potential issues (Oct 14, 2024):
1. **Time Alignment**: 
   - Ensure that all datasets (wave height, wind speed, atmospheric pressure, etc.) share a common timestamp. It’s important to choose a consistent time interval (e.g., hourly or daily) and aggregate or interpolate data to fit that interval if necessary.
   - For missing or mismatched timestamps, we can use interpolation techniques like linear or spline interpolation to fill gaps in the dataset.

2. **Data Merging**: 
   - After collecting data from each source, merge them on the timestamp field. Depending on the granularity of the timestamps, we may need to resample data to a consistent frequency before merging.
   - Use outer joins to ensure we capture all relevant data, or inner joins if we only want time periods where data from all sources is available.

3. **Feature Engineering**:
   - Consider adding lagged variables (e.g., wind speed from the previous hour or day) to capture time dependencies. This can be useful in time-series forecasting models like LSTM or ARIMA.
   - Additionally, we can create derived features like wind pressure gradients or temperature differentials to enhance predictive power.

4. **Normalization**:
   - Since we are collecting data from multiple sources, the units and scales might vary. Normalize or standardize your features to ensure compatibility between variables when feeding them into machine learning models.

5. **Data Quality**:
   - Pay attention to data gaps, outliers, and inconsistencies between datasets. Automated data cleaning pipelines can help identify and rectify issues in real-time.

6. **Alternative Solution**
   - If we are not able to align the data properly, we could try to find a single data source that captures the data we need.





