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
  

Analysis the 2023 data from Station 42042 at 29.207 N 88.237 W (29°12'24" N 88°14'12" W)

1. Overview: To build a multiple linear regression model with wave height (WVHT) as the dependent variable, we first need to prepare the data, ensuring that the dataset includes independent variables such as wind direction (WDIR), average wind speed (WSPD), maximum gust speed (GST), dominant period (DPD), average period (APD), main wind direction (MWD), pressure (PRES), air temperature (ATMP), and water temperature (WTMP), along with wave height (WVHT). Next, we conduct exploratory data analysis (EDA) to understand relationships between variables using statistical charts and descriptive statistics, as well as to check data quality, handling missing values and outliers. Based on EDA results, we select suitable features, possibly performing feature engineering if needed. Then, we split the dataset into training and testing sets, often with a 70% training and 30% testing ratio. We use the training set to build the multiple linear regression model, which can be implemented using the LinearRegression class from Python’s sklearn library. After building the model, we evaluate its performance on the test set, focusing on metrics such as mean squared error (MSE) and the coefficient of determination (R²), and analyze residual plots to ensure the model meets the basic assumptions of linear regression. If the model performs poorly, it can be optimized by adjusting feature selection, addressing multicollinearity, or trying alternative models. Finally, we interpret the model coefficients to understand which factors have the greatest impact on wave height and provide practical application recommendations accordingly. Throughout the process, it is essential to avoid overfitting and to ensure the model’s generalizability.
2. Correlation analysis of data
![Correlation Matrix](image/correlation_matrix%201.png)

Box plots are used to identify and remove outliers in the data that may adversely affect the performance of the model.
![Box Plot](image/Box_plot%201.png)

After removing the outliers:
![Box Plot after removing outliers](image/Box_plot%202.png)

![Correlation Matrix after removing outliers](image/correlation_matrix%202.png)

3.Modeling
1) linear regression model
Model Parameters:
[ 1.24867034e-04, 6.22953758e-02, -2.56387520e-02, -7.93630248e-04, 1.03557317e+00, 6.70419148e-05, -4.46014581e-04, 1.56621157e-02, 2.65817156e-05, -1.24772118e-02]

Model Intercept:
-3.386844226310629

Mean Squared Error (MSE):
0.09983868755979808

The model parameters represent the effect of each independent variable on the dependent variable (wave height, WVHT). Specifically:  
Wind Direction (WDIR): The coefficient is 1.24867034 × 10^−4, meaning that a 1-degree increase in wind direction predicts an increase in wave height of about 0.00012 meters, a very small effect.  
Average Wind Speed (WSPD): The coefficient is 6.22953758 × 10^−2, indicating that a 1 m/s increase in average wind speed predicts an increase in wave height of about 0.062 meters.  
Maximum Gust Speed (GST): The coefficient is −2.56387520 × 10^−2, meaning that a 1 m/s increase in maximum gust speed predicts a decrease in wave height of about 0.026 meters. This could be because gusts are often short-lived, impacting wave height less than sustained average wind speed.  
Dominant Period (DPD): The coefficient is 1.03557317, indicating that a 1-second increase in the dominant period predicts a significant increase in wave height of about 1.036 meters, the most influential variable.  
Average Period (APD): The coefficient is 6.70419148 × 10^−5, suggesting that a 1-second increase in average period predicts an increase in wave height of about 0.000067 meters, which is relatively small.  
Main Wind Direction (MWD): The coefficient is −4.46014581 × 10^−4, meaning that a 1-degree change in main wind direction predicts a decrease in wave height of about 0.00045 meters.
Pressure (PRES): The coefficient is 1.56621157 × 10^−2, indicating that a 1 hPa increase in pressure predicts an increase in wave height of about 0.016 meters.  
Air Temperature (ATMP): The coefficient is 2.65817156 × 10^−5, meaning that a 1°C increase in air temperature predicts an increase in wave height of about 0.000027 meters, an almost negligible effect.  
Water Temperature (WTMP): The coefficient is −1.24772118 × 10^−2, meaning that a 1°C increase in water temperature predicts a decrease in wave height of about 0.012 meters.
Model Intercept  
The model intercept is −3.386844226310629, which implies that when all independent variables are zero, the predicted wave height would be −3.39 meters. However, in real situations, it is unlikely that all variables would be zero, so the intercept is more of a mathematical concept rather than of practical significance.  
Mean Squared Error (MSE)  
The model’s mean squared error (MSE) is 0.09983868755979808, representing the average squared difference between the predicted and actual values. A lower MSE value indicates that the model's predictions are close to the true values, suggesting good predictive accuracy.  
Conclusion  
The multiple linear regression model effectively revealed that the dominant period and mean wind speed are the key factors affecting wave height prediction, while other variables such as wind direction, air pressure and water temperature also have a certain impact on wave height, but to a relatively small extent. This analysis provides an important scientific basis for understanding and predicting wave height.
![Predicting value and actual value](image/LinearRegression_prediction1.png)


2)RandomForestRegressor  
Mean Squared Error (MSE): 0.0034733644264875645
![Predicting value and actual value](image/RandomForestRegressor_prediction1.png)

The application of the Random Forest model in wave height prediction has significantly improved model performance. Compared to the multiple linear regression model, the Random Forest model's mean squared error is only 0.0034733644264875645, much lower than the linear regression model's 0.09983868755979808. This result indicates that the Random Forest model has a stronger advantage in handling complex nonlinear relationships and interactions between variables. The advantage of the Random Forest model lies in its ability to capture nonlinear relationships in the data while reducing the risk of overfitting through the integration of multiple decision trees, thereby enhancing the model's generalizability. Consequently, the Random Forest model is more reliable for wave height prediction and can provide more accurate results for oceanographic research and practical applications.

Conclusion:  
The Random Forest model has demonstrated excellent performance in wave height prediction tasks, especially in handling complex data relationships, outperforming the traditional multiple linear regression model. This provides a basis for selecting a more suitable model in practical applications. In future work, further exploration of parameter tuning for the Random Forest model could be undertaken to achieve even higher prediction accuracy. Additionally, combining the Random Forest model with other machine learning methods could be considered to enhance the accuracy and robustness of wave height predictions.


* Alternative models
Although the model we fit has a low MSE, the real life implication may be undermined. From the correlation matrix, we used DPD, APD (wave period) as parameters which has a correlation with WVHT very close to 1. DPD APD are essentially wave data, to prevent overfitting and make our model work without wave data, we created a different set of models without using DPD and APD (prediction.ipynb).

1. Data analysis

2. Model Fitting


* Future plans to the model:
1. Expanding data selection:

2. Test with other models:

3. Feature Engineering:









