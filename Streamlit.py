import pymysql
import pandas as pd
import streamlit as st
import plotly.express as px

# Create MySQL connection using pymysql
def create_connection():
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user="root",
            password='',
            database="policeledger",
            cursorclass=pymysql.cursors.DictCursor  # To get column names
        )
        return connection
    except Exception as exp:
        st.error("Database Connection error: {exp}")
        return None

# Fetch data from the database using function
def fetch_data(query):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cur:
                cur.execute(query)
                result = cur.fetchall()
                df = pd.DataFrame(result)
                return df
        finally:
            connection.close()
    else:
        return pd.DataFrame()
    
#Streamlit code

st.set_page_config(page_title="Police Ledger Dashboard", layout= "wide" )

#Background image
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://wallpapers.com/images/hd/ips-logo-simple-beige-wjb91e4j0pxgqm2v.jpg");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    </style>
    """, unsafe_allow_html=True
)
# Title
st.title("SecureCheck: Police Post Log Ledger") 

# Sidebar Menu
menu = st.sidebar.selectbox("Explore🔍", ["Home🏛️","Police Logs Overview🗂️","Metrics📊","Medium level analysis📉","Complex level analysis🧩","Predict Outcome🎯"])

# Home
if menu == "Home🏛️":
    st.subheader("**WELCOME**")

elif menu == "Police Logs Overview🗂️":
    st.header("_Digital Ledger for Police Post Logs_") 
    query = "SELECT * FROM police_post_logs"
    data = fetch_data(query)
    st.dataframe(data, use_container_width=True)
    st.markdown("**The table above showcases daily police log records, including incident types, dates, and locations.**")

# Metrics
elif menu == "Metrics📊": 
    # Fetch data
    query = "SELECT * FROM police_post_logs"
    data = fetch_data(query)

    # Quick Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Police Stops", data.shape[0])

    with col2:
        arrests = data[data["stop_outcome"].str.contains("arrest", case=False, na=False)].shape[0]
        st.metric("Total Arrests", arrests)

    with col3:
        warnings = data[data["stop_outcome"].str.contains("warning", case=False, na=False)].shape[0]
        st.metric("Total Warnings", warnings)

    with col4:
        drug_stop = data[data["drugs_related_stop"] == 1].shape[0]
        st.metric("Drug Related Stops", drug_stop)

# Plotting 

# Stop Outcome Distribution
    outcome_counts = data["stop_outcome"].value_counts().reset_index()
    outcome_counts.columns = ["Stop Outcome", "Count"]
    fig1 = px.pie(outcome_counts, names="Stop Outcome", values="Count",title="Stop Outcome Distribution")
    st.plotly_chart(fig1, use_container_width=True)


# Medium level analysis

elif menu == "Medium level analysis📉":
    medium_queries = st.selectbox("Select your question to run:",
        [
            "Top 10 vehicle number involed in drug related stops" ,
            "Driver age group with highest arrest rate" ,
            "Gender distribution of drivers stopped in each country",
            "Race and gender combination with highest search rate",
            "Time of day with most traffic stops",
            "Average Stop Duration for different Violations",
            "Night Stops More Likely to Lead to Arrests",
            "Violations which most associated with searches or arrests" ,
            "Most common violations for young drivers < 25",
            "Violation that rarely resulting in search or arrest",
            "Countries that report with highest drug-related stop rates" ,
            "Arrest rate by country and violation",
             "Country has the most stops with search conducted" ,
        ]
    )
    query_map = {
        "Top 10 vehicle number involed in drug related stops" : """SELECT vehicle_number, COUNT(*) AS drugs_related_stop
                                                        FROM police_post_logs WHERE drugs_related_stop = TRUE 
                                                        GROUP BY vehicle_number
                                                        ORDER BY drugs_related_stop DESC LIMIT 10""",

        "Driver age group with highest arrest rate" :"""SELECT CASE
                                                    WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
                                                    WHEN driver_age BETWEEN 26 AND 35 THEN '26-35'
                                                    WHEN driver_age BETWEEN 36 AND 45 THEN '36-45'
                                                    WHEN driver_age BETWEEN 46 AND 60 THEN '46-60'
                                                    ELSE '60+'
                                                    END AS age_group,
                                                    COUNT(*) AS total_driver,
                                                    SUM(is_arrested) AS total_arrests,
                                                    ROUND(SUM(is_arrested)*100.0/COUNT(*), 2) AS arrest_rate_percent
                                                    FROM police_post_logs
                                                    GROUP BY age_group
                                                    ORDER BY arrest_rate_percent DESC
                                                    LIMIT 1""",
 
        "Gender distribution of drivers stopped in each country" :"""SELECT country_name, driver_gender, COUNT(*) AS total_gender,
                                                               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY country_name), 2) AS gender_percent
                                                                FROM police_post_logs
                                                                GROUP BY country_name, driver_gender
                                                                ORDER BY country_name, driver_gender""",     

        "Race and gender combination with highest search rate" :"""SELECT driver_race, driver_gender, COUNT(*) AS total_stops,
                                                            SUM(CASE WHEN search_conducted  = 1 THEN 1 ELSE 0 END) AS total_searches,
                                                            ROUND(SUM(CASE WHEN search_conducted  = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS search_percent_rate
                                                            FROM police_post_logs
                                                            WHERE driver_race IS NOT NULL AND driver_gender IS NOT NULL
                                                            GROUP BY driver_race, driver_gender
                                                            ORDER BY search_percent_rate DESC LIMIT 1""",

                                                
        "Time of day with most traffic stops" :"""SELECT HOUR(STR_TO_DATE(stop_time, '%Y-%m-%D %H:%m:%S')) AS stop_hour, COUNT(*) AS total_stops
                                                FROM police_post_logs
                                                WHERE stop_time IS NOT NULL
                                                GROUP BY stop_hour 
                                                ORDER BY total_stops DESC LIMIT 1""",

        "Average Stop Duration for different Violations" : """SELECT violation,
                                                            AVG(stop_duration) AS average_stop_duration
                                                            FROM police_post_logs
                                                            WHERE stop_duration IS NOT NULL 
                                                            GROUP BY violation ORDER BY Average_stop_duration DESC""",

        "Night Stops More Likely to Lead to Arrests" : """SELECT CASE
                                                    WHEN HOUR(stop_time) BETWEEN 20 AND 23 OR HOUR(stop_time) BETWEEN 0 AND 5 THEN 'Night'
                                                    ELSE 'Day' END AS time_of_day,COUNT(*) AS total_stops,
                                                    SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS total_arrests,
                                                    ROUND(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate_percent
                                                    FROM police_post_logs
                                                    WHERE stop_time IS NOT NULL
                                                    GROUP BY time_of_day
                                                    ORDER BY arrest_rate_percent DESC""",

        "Violations which most associated with searches or arrests" :"""SELECT violation,COUNT(*) AS total_stops,
                                                                 SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS total_arrests, 
                                                                 SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches, 
                                                                 SUM(CASE WHEN is_arrested = 1 OR search_conducted = TRUE THEN 1 ELSE 0 END) AS search_or_arrest_total
                                                                 FROM police_post_logs
                                                                 GROUP BY violation
                                                                 ORDER BY search_or_arrest_total DESC LIMIT 10""",                                                    

        "Most common violations for young drivers < 25" :"""SELECT violation,COUNT(*) AS total_stops
                                                        FROM police_post_logs
                                                        WHERE driver_age < 25
                                                        GROUP BY violation
                                                        ORDER BY total_stops DESC LIMIT 10""",

        "Violation that rarely resulting in search or arrest" :"""SELECT violation,COUNT(*) AS total_stops,
                                                            SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS total_arrests
                                                            FROM police_post_logs
                                                            GROUP BY violation
                                                            ORDER BY total_arrests ASC LIMIT 1""",

        "Countries that report with highest drug-related stop rates" :"""SELECT country_name,COUNT(*) AS total_stops,
                                                                   SUM(CASE WHEN drugs_related_stop = 1 THEN 1 ELSE 0 END) AS drug_related_stops,
                                                                   ROUND(SUM(CASE WHEN drugs_related_stop = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS drug_stop_rate_percent
                                                                   FROM police_post_logs
                                                                   GROUP BY country_name
                                                                   ORDER BY drug_stop_rate_percent DESC""",

        "Arrest rate by country and violation" :"""SELECT country_name,COUNT(*) AS total_stops,violation,
                                               SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS total_arrests,
                                               ROUND(100.0 * SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS total_arrest_percent
                                               FROM police_post_logs
                                               GROUP BY country_name, violation
                                               ORDER BY country_name""",
 
        "Country has the most stops with search conducted" :"""select country_name, count(*) as total_stops
                                                              from police_post_logs
                                                              group by country_name
                                                              order by total_stops
                                                              desc limit 1""",
}
    

    if st.button("Run"):
        result = fetch_data(query_map[medium_queries])
        if result is not None and not result.empty:
            st.write(result)
        else:
            st.warning("No result was found")


# Complex level analysis


elif menu == "Complex level analysis🧩":
    complex_queries = st.selectbox("Select your question to run:",
        [
            "Yearly breakdown of stops and arrests by country",
            "Driver violation trends by age and race",
            "Time period analysis of stops, no of stops by yr, month, hr of the day",
            "Violations with high search & arrest rates",
            "Driver demographics by country (Age, Gender and Race)",
            "Top 5 violations with highest arrest rates"
        ]
    )
    query_map_1 = {
        "Yearly breakdown of stops and arrests by country" : """SELECT country_name, 
                                                                EXTRACT(YEAR FROM Stop_date) AS stop_date, COUNT(*) AS total_stops, 
                                                                SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests, 
                                                                ROUND(SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS Arrest_rate_percent, 
                                                                RANK() OVER (PARTITION BY Stop_date ORDER BY SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) DESC) AS Arrest_rank 
                                                                FROM police_post_logs 
                                                                GROUP BY Country_name, Stop_date 
                                                                ORDER BY Stop_date, Arrest_rank""",

        "Driver violation trends by age and race" : """WITH Age_race_summary AS (SELECT Driver_age, Driver_race, Violation, COUNT(*) AS Violation_count 
                                                        FROM police_post_logs GROUP BY driver_age, driver_race, violation)
                                                        SELECT ars.driver_age, ars.driver_race, ars.violation, ars.violation_count 
                                                        FROM Age_race_summary ars 
                                                        JOIN (SELECT driver_age, driver_race, MAX(violation_count) AS Max_count 
                                                        FROM age_race_summary GROUP BY driver_age, driver_race)
                                                        top_violations ON ars.driver_age = top_violations.driver_age 
                                                        AND ars.driver_race = top_violations.driver_race 
                                                        AND ars.violation_count = top_violations.max_count 
                                                        ORDER BY ars.driver_race, ars.driver_age""",
    
        "Time period analysis of stops, no of stops by yr, month, hr of the day" : """SELECT EXTRACT(YEAR FROM stop_date) AS Year, 
                                                                                    EXTRACT(MONTH FROM stop_date) AS Month, 
                                                                                    EXTRACT(HOUR FROM stop_time) AS Hour, COUNT(*) AS stop_count 
                                                                                    FROM police_post_logs 
                                                                                    GROUP BY Year, Month, Hour ORDER BY Year, Month, Hour""",
      
        "Violations with high search & arrest rates" : """SELECT violation, COUNT(*) AS Total_stops, 
                                                            SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS Total_searches, 
                                                            SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS Total_arrests, 
                                                            ROUND(SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS Search_rate, 
                                                            ROUND(SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate, 
                                                            RANK() OVER (ORDER BY SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) DESC) AS Arrest_rank
                                                            FROM police_post_logs
                                                            GROUP BY violation 
                                                            ORDER BY Arrest_rank LIMIT 10""",
    
        "Driver demographics by country (Age, Gender and Race)" : """SELECT country_name, AVG(driver_age) AS Avg_age, Driver_gender, Driver_race, COUNT(*) AS Stop_count
                                                                        FROM police_post_logs 
                                                                        GROUP BY Country_name, Driver_gender, Driver_race 
                                                                        ORDER BY Country_name, Stop_count DESC""",
    
        "Top 5 violations with highest arrest rates" : """SELECT violation, COUNT(*) AS Total_stops, 
                                                            SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS Total_arrests, 
                                                            ROUND(SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS Arrest_rate_percent 
                                                            FROM police_post_logs 
                                                            GROUP BY Violation 
                                                            ORDER BY Arrest_rate_percent DESC LIMIT 5"""

}

    if st.button("Run"):
        result = fetch_data(query_map_1[complex_queries])
        if result is not None and not result.empty:
            st.write(result)
        else:
            st.warning("No result was found")

# Predict Outcome
elif menu=="Predict Outcome🎯": 

    query="select * from police_post_logs"
    data=fetch_data(query)

    st.markdown("Fill the fields below to log a stop and predict the outcome and violation.")

    # Input Form

    with st.form("Log_Form"):
                
        vehicle_number=st.text_input("Vehicle Number")
        stop_date=st.date_input("Stop Date")
        stop_time=st.time_input("Stop Time")
        country_name=st.selectbox("Country Name", ["Canada", "USA", "India"])                
        driver_age=st.number_input("Driver Age", min_value=16, max_value=100, value=20)
        driver_race=st.selectbox("Driver Race", ["Asian", "Black", "White", "Hispanic", "Other"])
        search_type=st.selectbox("Search Type", ["Vehicle Search", "Frisk", "None"])
        stop_duration=st.selectbox("Stop Duration",data["stop_duration"].dropna().unique())
        driver_gender=st.radio("Driver Gender",["Male","Female"])
        st.write(driver_gender)
        drugs_related_stop = st.selectbox("Is the stop is drug related?",["YES", "NO"])
        search_conducted = st.selectbox("Is the search is conducted?", ["YES", "NO"])
        submitted=st.form_submit_button("Predict Stop Outcome & Violation")

    filtered_data = pd.DataFrame()     
    if submitted:
        filtered_data= data[
                            (data["driver_gender"]== driver_gender)&
                            (data["driver_age"]== driver_age)&
                            (data["search_conducted"]==(search_conducted))&
                            (data["stop_duration"]==stop_duration)&
                            (data["drugs_related_stop"]==drugs_related_stop)
            ]

    #Predict Stop Outcome and Violation

    if not filtered_data.empty:
        predicted_outcome = filtered_data["Stop Outcome"].mode()[0]
        predicted_violation = filtered_data["Violation"].mode()[0]
    else:
        predicted_outcome = "Warning"
        predicted_violation = "Speeding"

    #Prediction summary

    search_text = "A search was conducted" if search_conducted.upper() == "YES" else "no search was conducted"
    drug_text = "it's drug-related" if drugs_related_stop.upper() == "YES" else "it's not drug-related"

    st.markdown("**_Prediction Summary_**")

    st.markdown(f"""
        -**Vehicle Number:** {vehicle_number}                
        -**Predicted Violation:** {predicted_violation}
        -**Predicted Stop Outcome:** {predicted_outcome}
        -**Stop Duration:** {stop_duration}

    A **{driver_age}**-year-old **{driver_gender}** driver in **{country_name}** was stopped for **{predicted_violation}** at {stop_time.strftime('%I:%M %p')} on {stop_date}.
        **{search_text}**, received a **{predicted_outcome}** and **{drug_text}**.                   
    """) 
    


