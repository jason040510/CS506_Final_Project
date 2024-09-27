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



