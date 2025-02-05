# -*- coding: utf-8 -*-
#import libraries
import requests 
import csv 
import sqlite3
import logging

# Configure logging errors 
logging.basicConfig(filename='country_query.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

#function database connection
def execute_query(conn, query):
    try:
        cursor = conn.cursor() 
        cursor.execute(query)  
        return cursor.fetchall()  
    except sqlite3.Error as e:
        logging.error(f"Error executing the query: {str(e)}")

def save_results_to_txt(results, txt_file):
    try:
        with open(txt_file, 'w', newline='', encoding='utf-8') as file:  
            writer = csv.writer(file, delimiter='\t')  
            writer.writerow(['Country Code', 'Country Name'])  

            for row in results:  
                writer.writerow(row)  

        logging.info(f"Query results saved to {txt_file}")  
    except IOError:
        logging.error("Error saving query results to TXT file.")

# Fetch city population data and store in the database
def fetch_and_store_data(conn, api_url):
    try:
        cursor = conn.cursor()
        # Fetch data from API as a CSV file
        response = requests.get(api_url)
        csv_data = response.content.decode('utf-8')

        # Read the CSV data and insert into the database
        reader = csv.reader(csv_data.splitlines(), delimiter=';')
        next(reader)  # Skip the header row if it exists

        for row in reader:
            
            geoname_id = int(row[0])
            name = row[1]
            ascii_name = row[2]
            alternate_names = row[3]
            feature_class = row[4]
            feature_code = row[5]
            country_code = row[6]
            country_name_en = row[7]
            country_code_2 = row[8]
            admin1_code = row[9]
            admin2_code = row[10]
            admin3_code = row[11]
            admin4_code = row[12]
            population = int(row[13])
            elevation = row[14]
            digital_elevation_model = int(row[15])
            timezone = row[16]
            modification_date = row[17]
            label_en = row[18]
            coordinates = row[19]

            # Insert data into the table
            cursor.execute("INSERT INTO city_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (geoname_id, name, ascii_name, alternate_names, feature_class, feature_code, country_code,
                            country_name_en, country_code_2, admin1_code, admin2_code, admin3_code, admin4_code,
                            population, elevation, digital_elevation_model, timezone, modification_date, label_en, coordinates))

        # Commit the changes
        conn.commit()
        

        logging.info("Data fetched and stored successfully!")

    except requests.exceptions.RequestException as e:
      logging.error("Error fetching data from the API:", str(e))
    except csv.Error as e:
      logging.error("Error reading CSV data:", str(e))
    except sqlite3.Error as e:
      logging.error("Error storing data in the database:", str(e))

#extract from database countries without megapolises
def countries_without_megapolises(conn,query):
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        output_file = 'countries_without_megapolises.txt'

        # Write the results to a TXT file
        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file, delimiter='\t')

            # Write the header
            writer.writerow(['Country Code', 'Country Name'])

            # Write the data rows
            writer.writerows(rows)

        logging.info(f"Query results saved to {output_file} successfully!")

    except sqlite3.Error as e:
        logging.error("Error executing the query:", str(e))

def main():
   
    # API url
    api_url = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/geonames-all-cities-with-a-population-1000/exports/csv?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"  

    try:

        # Database connection
        conn = sqlite3.connect('city_data.db')
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS city_data
                        (geoname_id INTEGER, name TEXT, ascii_name TEXT, alternate_names TEXT,
                        feature_class TEXT, feature_code TEXT, country_code TEXT, country_name_en TEXT,
                        country_code_2 TEXT, admin1_code TEXT, admin2_code TEXT, admin3_code TEXT,
                        admin4_code TEXT, population INTEGER, elevation INTEGER, digital_elevation_model INTEGER,
                        timezone TEXT, modification_date TEXT, label_en TEXT, coordinates TEXT)''')

        fetch_and_store_data(conn, api_url)
        
        

        # Query to find countries without a megacity
        query = '''
            SELECT DISTINCT country_code, country_name_en 
            FROM city_data
            WHERE country_code NOT IN
            (
              SELECT DISTINCT country_code
              FROM city_data
              WHERE population >= 10000000
            )
            ORDER BY country_name_en
        '''
        countries_without_megapolises(conn,query)
    except sqlite3.Error as e:   
        logging.error(f"Error connecting to the database: {str(e)}") 
    finally:
        # Close the database connection
        if conn:
            conn.close()  

if __name__ == '__main__':
    main()

