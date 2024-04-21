import requests
import sqlite3
import time
import json
import argparse
import sys
import socket

root_url = "https://api.content.tripadvisor.com/api/v1"

class APIExtractor():
    def __init__(self,api_key_file,input_db,**kwargs):
        self.api_key = self.get_api_key(api_key_file)
        self.input_db = input_db

    def get_ip_address(self):
        try:
            response = requests.get('https://api.ipify.org')
            if response.status_code == 200:
                return response.text
            else:
                print("Failed to retrieve IP address:", response.status_code)
                return None
        except Exception as e:
            print("Error:", e)
            return None

    def get_api_key(self,api_key_file):
        with open(api_key_file,'r') as f:
            api_key = f.read().strip()
        return api_key

    def get_detail_url(self,api_key,location_id):
        return f"{root_url}/location/{location_id}/details?key={api_key}&language=en&currency=USD"

    def get_search_url(self,api_key,search_string):
        return f"{root_url}/location/search?key={api_key}&searchQuery={search_string}&category=hotels&language=en"

    def get_review_url(self,api_key,location_id):
        return f"{root_url}/location/{location_id}/reviews?key={api_key}&language=en&currency=USD"



    def get_tripadvisor_hotels_info(self,api_key,search_string): 

        url = self.get_search_url(api_key,search_string)
        headers = {"accept": "application/json"}
        # print(response.text)
        print(url,headers)

        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            if data.get('Message'):
                print(data.get('Message'))
                print(f"Check Api key [{api_key}] and IP {self.get_ip_address()}")
                sys.exit()
            print(f'Search Response: expecting 10 location _id: {data}')
            return_data = []
            # Extract hotel information
            for hotel in data.get("data", []):
                time.sleep(0.2)
                location_id = hotel.get("location_id", "N/A")
                url = self.get_detail_url(api_key,location_id)
                print(f"Detail URL for API call: {url}")
                response = requests.get(url, headers=headers)
                data = response.json()
                return_data.append(data)
                # print("-" * 30)

        except requests.RequestException as e:
            print(f"Error fetching data: {e}")

        return return_data

    def get_tripadvisor_hotels_review(self,api_key,location_id,debug=False): 
        headers = {"accept": "application/json"}
        
        # Extract hotel review

        url = self.get_review_url(api_key,location_id)           
        response = requests.get(url, headers=headers)
        data = response.json()
        if debug:
            print(response.json())
        
        if 'error' in data:    
            return data
        else:
            return data['data']

    def generate_json_with_hotel_info(self,start,end):
        query_string = 'select hotel_name,address from  info6 where amenities_list is  NULL'
        conn = sqlite3.connect(self.input_db)
        cursor = conn.cursor()
        results = cursor.execute(query_string)
        
        conn.commit()
        count = 0
        # print(f'Need info from {len(results)} hotels.')
        for e in results:
            count += 1
            if count < start : continue   # start at here
            if count > end : break   # end here
            time.sleep(0.2)
            search_string = e[0] +', '+ e[1]
            
            file_name = "info_"+search_string.replace(',','_').replace(' ','_').replace('/','_')+".json"
            # Location Search
            info = self.get_tripadvisor_hotels_info(self.api_key,search_string )
            print(info)
            # Location
            if not info:
                print("no result found. We may have reached limit")
                break   
            # with open(file_name,"w") as j:
            #     json.dump(info,j)
            print(f"[{count}]: saved info of {len(info)} hotels in {file_name} with {info[0]['name']} as first element") 
            
        cursor.close()
        conn.close()        

def main():

    parser = argparse.ArgumentParser(description="Process API output files to create database")
    parser.add_argument("--api_key_file", action="store", help="API Key File")
    parser.add_argument("--input_db", action="store", 
                        help="Input Database. We check this database , identify \
                        rows that has amenities blanc. \
                        And try to collect data from Tripadvsor api.")
    args = parser.parse_args()


    api_key_file = args.api_key_file #'tripadvisor_api_key.txt'
    input_db = args.input_db #'/home/mir/grepo/webcrawlers/hotels/hotels_data6.db'
    
    proc = APIExtractor(api_key_file=api_key_file,input_db=input_db)
    
    proc.generate_json_with_hotel_info(start=201,end=201)

if __name__ == '__main__':
    main()


