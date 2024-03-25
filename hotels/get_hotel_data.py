import requests
from pprint import pprint
import re
import json
import pandas as pd
import time
import sys
import os
import sqlite3

# selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent

# ==================== API Functions====================

options = Options()
# options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

ua = UserAgent()
user_agent = ua.random
print(user_agent)

options.add_argument(f'--user-agent={user_agent}')

# Adding argument to disable the AutomationControlled flag 
options.add_argument("--disable-blink-features=AutomationControlled") 
 
# Exclude the collection of enable-automation switches 
options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
 
# Turn-off userAutomationExtension 
options.add_experimental_option("useAutomationExtension", False) 


# ======== Selenium Helper Function ========================
def get_location_dict(text = ''):
    

    location_text = text #"Location\n100\nGreat for walkers\nGrade: 100 out of 100\n292\nRestaurants\nwithin 0.3 miles\n116\nAttractions\nwithin 0.3 miles\n17 East Monroe Street, Chicago, IL 60603\n1 (855) 605-0316\nGetting there\nMidway Airport9 mi\nSee all flights\nO'Hare Intl Airport16 mi\nSee all flights\nMonroeChicago L1 min\nAdams/WabashChicago L2 min\nRental Cars\nSee rental cars from $34/day\nSee all nearby hotels\nNearby restaurants\nThe Dearborn\n591 reviews\n6 min\nAmerican\nAcanto\n539 reviews\n3 min\nTuscan\nThe Gage\n2,384 reviews\n3 min\nAmerican\nRemington's\n539 reviews\n4 min\nAmerican\nSee all nearby restaurants\nNearby attractions\nThe Art Institute of Chicago\n24,560 reviews\n4 min\nArt Museums\nMillennium Park\n25,142 reviews\n6 min\nParks\nCloud Gate\n18,285 reviews\n5 min\nMonuments & Statues\nThe Magic Parlour\n629 reviews\n2 min\nTheater & Performances\nSee all nearby attractions"
    temp_dict = {}
    temp_list = location_text.split('\n')
    temp_dict['walking_grade'] = list(re.findall('Location\n(.+)\n(.+)\n(.+)\n',location_text)[0])
    temp_dict['nearby_restaurants_summary'] = list(re.findall('\n(.+)\n(Restaurants)\n(within.+miles)\n',location_text)[0])
    temp_dict['nearby_attractions_summary'] = list(re.findall('\n(.+)\n(Attractions)\n(within.+miles)\n',location_text)[0])
    temp_dict['contact'] = temp_list[10] 
    temp_dict['getting there']= re.findall(r'(Getting there(\n.+)*\nSee all nearby hotels)',location_text)[0][0].split("\n")[1:]
    temp_dict['nearby_restaurants']= re.findall(r'(Nearby restaurants(\n.+)*\nSee all nearby restaurants)',location_text)[0][0].split("\n")[1:]
    temp_dict['nearby_attractions']= re.findall(r'(Nearby attractions(\n.+)*\nSee all nearby attractions)',location_text)[0][0].split("\n")[1:]
    
    # pprint(temp_dict)
    return temp_dict

def get_info(url):
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    time.sleep(1)
    driver.get(url)
    time.sleep(5)
    # _xpath = '//*[@id="HEADING"]'
    info_dict = {}
    review_dict = {}
    info_dict['location_id'] = re.findall(r'_Review-g.+-d(\d+)-',url)[0]
    info_dict['hotel_name'] = driver.find_element(By.XPATH,'//*[@id="HEADING"]').text
    info_dict['phone_number'] = driver.find_element(By.XPATH,'//*[@id="lithium-root"]/main/span/div[4]/div[1]/div/div[3]/div/div[3]/div[1]/div[3]/div[2]/a/div/div').text
    info_dict['faq_text'] = driver.find_element(By.XPATH,'//*[@id="FAQ"]').text
    location_text = driver.find_element(By.XPATH,'//*[@id="LOCATION"]').text
    review_text = driver.find_element(By.XPATH,'//*[@id="LOCATION"]').text
    
    location_dict = get_location_dict(text = location_text)
    info_dict.update(location_dict)
    driver.close()


    return info_dict

def get_review_from_text(input_text):
    
    list_input_text = input_text.split("\n")
    name,time = re.findall('(.+) wrote a review(.+)$',list_input_text[0])[0]
    contributions,helpful_votes = \
        re.findall(r'(\d+) contributions(\d+) helpful votes$',list_input_text[1])[0]
    response_review = ''
    has_response = False
    response_date = None
    
    post_helpful = 0
    responded_person = None
    for text in list_input_text[2:]:
        if text.startswith('Date of stay:'):
            date = re.findall(r'Date of stay: (.+)$',text)[0]
        elif text.startswith('Response from'):
            responded_person = re.findall(r'Response from (.+)$',text)[0]
        elif text.startswith('Responded '):
            response_date = re.findall(r'Responded (.+)$',text)[0]
            has_response = True
        elif text.startswith('This response is the subjective opinion'):
            response_review += f"\n {text}"
        elif text.startswith('Report response as inappropriate'):
            response_review += f"\n {text}"
        elif has_response and (not text.startswith('Read more')):
            response_review += text
        elif re.findall(r'^(\d+)$',text):
            post_helpful = re.findall(r'^(\d+)$',text)[0]
                    
    return_dict = {
        'date':date,
        'name':name,
        'time': time,
        'helpful_votes': float(helpful_votes),
        'contributions': contributions,
        'responded_person': responded_person,
        'response_date':response_date,
        'response_review':response_review,
        'post_helpful':post_helpful
        
        
        }
    return return_dict

    

# ======== Selenium Helper Function ========================
# def update_review_csv(url ):
#     for page in  range(2):
#         if page == 0:        
#             _xpath = f'//*[@id="lithium-root"]/main/span/div[4]/div[3]/div/div[1]/div/div/div[1]/div[3]/div[3]/div[1]/'
#         else:
#             # url = f"https://www.tripadvisor.com/Hotel_Review-g187147-d230431-Reviews-or{page}0-Hotel_Astoria_Astotel-Paris_Ile_de_France.html"
#             url = url.replace('-Reviews-',f'-Reviews-or{page}0-')
#             _xpath = f'//*[@id="lithium-root"]/main/span/div[3]/div[3]/div/div[1]/div/div/div[1]/div[3]/div[3]/div[1]/' 
#         driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)            
#         driver.get(url)
#         time.sleep(5)
#         for idiv in range(1,3):
#             xpath = _xpath + f'div[{idiv}]'
            
            
#             print(f'xpath: {xpath}')
#             print(f'=========Page: {page+1}, Review no: {idiv}============')
#             print(f'{xpath}')
#             xpath_element = driver.find_element(By.XPATH,xpath)
#             time.sleep(1)
#             print(xpath_element.text)
#             dict_hotel_reviews = {}
#         driver.close()
#         driver.quit()




root_url = "https://api.content.tripadvisor.com/api/v1"
def get_detail_url(api_key,location_id):
    return f"{root_url}/location/{location_id}/details?key={api_key}&language=en&currency=USD"


def get_search_url(api_key,search_string):
    return f"{root_url}/location/search?key={api_key}&searchQuery={search_string}&category=hotels&language=en"


def get_tripadvisor_hotels(api_key,city_state): 


    url = get_search_url(api_key,city_state)
    headers = {"accept": "application/json"}
    # print(response.text)
    # print(url)

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        return_data = []
        # Extract hotel information
        for hotel in data.get("data", []):
            time.sleep(0.2)
            location_id = hotel.get("location_id", "N/A")
            url = get_detail_url(api_key,location_id)
            # print(url)
            response = requests.get(url, headers=headers)
            data = response.json()
            return_data.append(data)
            # print("-" * 30)

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")

    return return_data

def get_cities(filename = 'cities.txt'):
    import re
    with open(filename, "r") as file:
        text = file.read()

    # Regular expression pattern to match city and state
    pattern = r"\d+,(\w+),(\w+),\d+"

    # Find all matches
    matches = re.findall(pattern, text)
    cities = []
    # Extract city and state from each match
    for city,state in matches:
        cities.append(f"{city}, {state}")
        
     
    return cities

def get_locations_ids(filename = 'cities.txt'):
    import re
    with open(filename, "r") as file:
        text = file.read()

    # Regular expression pattern to match city and state
    pattern = r"\d+,(\w+),(\w+),\d+"

    # Find all matches
    matches = re.findall(pattern, text)
    cities = []
    # Extract city and state from each match
    for city,state in matches:
        cities.append(f"{city}, {state}")
        
     
    return cities

def update_info_csv(csv_name = 'hotels_info.csv'):    
    print(f"hotel count: {len(dict_info_cities)}")
    list_of_dicts = []
    count = 0
    succeeded_hotel=[]
    failed_hotel=[]
    total = len(dict_info_cities)
    
    pre_existing = dict()
    if os.path.exists(csv_name):
        pre_csv_df = pd.read_csv(csv_name)
        for x in pre_csv_df['location_id']:            
            pre_existing[str(x)] = True

    for dict_city in dict_info_cities:
        count += 1
        time.sleep(2)
        location_id = dict_city.get('location_id')
        # print(location_id,type(location_id),pre_existing)
        if pre_existing.get(location_id,False):
            print(f"{count}. Item exists {location_id}")
            continue
        info_dict = {}
        info_dict['hotel_name']     =dict_city.get('name')
        info_dict['rating']         = dict_city.get('rating')
        info_dict['n_reviews']      = dict_city.get('num_reviews')
        info_dict['address']        =dict_city.get('address_obj').get('address_string')
        info_dict['ranking']        =dict_city.get('ranking_data',{'none':'no_rank'}).get('ranking_string')
        info_dict['about_text']     =dict_city.get('description')
        info_dict['amenities_list'] =dict_city.get('amenities')
        info_dict['contact']        = dict_city.get('address_obj').get('address_string')
        hotel_url = info_dict['web_url']= dict_city.get('web_url').replace('?m=66827','')
        info_dict['location_id']    =dict_city.get('location_id')
        info_dict['phone_number']   =dict_city.get('phone')

        print(f"will update with selenium scraping on {hotel_url}")

        
        try:
        
            temp_dict = get_info(url = hotel_url)

            info_dict.update(temp_dict)
            list_of_dicts.append(info_dict)
            succeeded_hotel.append(info_dict['location_id'])

        except :
            # print(f"Could not parse {info_dict['hotel_name']} 's url {info_dict['web_url']}")
            # print(f'Error {repr(e)}' )
            failed_hotel.append(info_dict['location_id'])

        finally:
            sys.stdout.write('\r')
            sys.stdout.write(f"Completed: [{count} of {total}]")
            sys.stdout.flush()

    
    temp_df = pd.DataFrame.from_dict(list_of_dicts)
    if os.path.exists(csv_name):
        df = pd.concat([pre_csv_df,temp_df])
    else:
        df = temp_df
    
    df = df[['hotel_name', 'rating', 'n_reviews', 'address', 'ranking','about_text', 'amenities_list', 'contact', 'web_url', 'location_id', 'phone_number', 'faq_text', 'walking_grade','nearby_restaurants_summary', 'nearby_attractions_summary','getting there', 'nearby_restaurants', 'nearby_attractions']]
    df.to_csv(csv_name)
    # # df.to_sql(con=conn,index=True,if_exists="replace",name="info")
    # # conn.close()
    # print(f'succeeded hotels {succeeded_hotel}')
    print(f'succeeded {len(succeeded_hotel)}/{len(dict_info_cities)}')

def set_viewport_size(driver, width, height):
    window_size = driver.execute_script("""
        return [window.outerWidth - window.innerWidth + arguments[0],
          window.outerHeight - window.innerHeight + arguments[1]];
        """, width, height)
    driver.set_window_size(*window_size)
def sqlite_update(data,table):
    db_file_name = "hotels_data_1.db"
    conn = sqlite3.connect(db_file_name)
    cursor = conn.cursor()
    insert_str = f"INSERT INTO reviews {str(tuple(data.keys()))} VALUES {str(tuple(data.values()))}"
    print(insert_str)
    cursor.execute(insert_str)
    conn.commit()
    cursor.close()
    conn.close()

    
    
    

def update_review_csv(csv_name = 'hotel_reviews.csv'):
    print(f"hotel count: {len(dict_info_cities)}")
    list_of_dicts = []
    count = 0
    succeeded_hotel=[]
    failed_hotel=[]
    total = len(dict_info_cities)
    
    pre_existing = dict()
    if os.path.exists(csv_name):
        pre_csv_df = pd.read_csv(csv_name)
        for x in pre_csv_df['location_id']:            
            pre_existing[str(x)] = True
    for dict_city in dict_info_cities:
        count += 1
        time.sleep(1)
        location_id = dict_city.get('location_id')
        # print(location_id,type(location_id),pre_existing)
        if pre_existing.get(location_id,False):
            print(f"{count}. Item exists {location_id}")
            continue
        review_dict = {}
        hotel_name = dict_city.get('name')
        hotel_url_0 =  dict_city.get('web_url').replace('?m=66827','')
        for page in range(4):
            if page == 0: 
                hotel_url = hotel_url_0       
                _xpath = f'//*[@id="lithium-root"]/main/span/div[4]/div[3]/div/div[1]/div/div/div[1]/div[3]/div[3]/div[1]'
            else:
                hotel_url = hotel_url_0.replace('-Reviews-',f'-Reviews-or{page}0-')
                _xpath = f'//*[@id="lithium-root"]/main/span/div[3]/div[3]/div/div[1]/div/div/div[1]/div[3]/div[3]/div[1]' 
                                                    
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)            
            time.sleep(0.20)
            set_viewport_size(driver, 800, 600)
            time.sleep(0.25)
            # Changing the property of the navigator value for webdriver to undefined 
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            time.sleep(0.23)
            try:
                driver.get(hotel_url)
                
                
                
                
            except:
                print(f"Could not get url {hotel_url}")
                driver.close()
                driver.quit()
                continue
            # finally:
            #     sys.stdout.write('\r')
            #     sys.stdout.write(f"Completed: [{count} of {total}]")
            #     sys.stdout.flush()
            time.sleep(5)
            # Iterate over this page's reviews
            for idiv in range(1,12):
                xpath = _xpath + f'/div[{idiv}]'
                try:
                    full_text = driver.find_element(By.XPATH,xpath).text
                
                    print(full_text)
                    temp = get_review_from_text(full_text)
                    
                    print(f'xpath: {xpath}')
                    print(f'=========Page: {page+1}, Review no: {idiv}============')
                    print(f'{xpath}')
                    review_id = f"{location_id}_{page+1}_{idiv}"
                    time.sleep(0.15)
                    # date = driver.find_element(By.XPATH,xpath + f'/div[2]/div[3]/div/span[@class="iSNGb _R Me S4 H3 Cj"]').text
                    # time.sleep(0.10)
                    # name = driver.find_element(By.XPATH,xpath + f'/div[1]/div/div[2]/div/div/span/a').text
                    time.sleep(0.12)
                    review_title = driver.find_element(By.XPATH,xpath + f'/div[2]/div[2]').text
                    time.sleep(0.17)
                    review = driver.find_element(By.XPATH,xpath + f'/div[2]/div[3]/div[1]/div[1]').text
                    time.sleep(0.15)
                    response_review = "TBD"#driver.find_element(By.XPATH,'//*[@id="lithium-root"]/main/span/div[3]/div[3]/div/div[1]/div/div/div[1]/div[3]/div[3]/div[1]/div[1]/div[2]/div[3]/div[4] ')
                    # post_helpful = driver.find_element(By.XPATH,'//*[@id="lithium-root"]/main/span/div[3]/div[3]/div/div[1]/div/div/div[1]/div[3]/div[3]/div/div[1]/div[2]/div[3]/div[3]/button[@class="BrOJk u j z _F wSSLS HuPlH Vonfv"]/span[@class="kLqdM"]/span[@class="biGQs _P FwFXZ"]').text
                    dict_hotel_reviews = {

                        'hotel_name' : hotel_name,
                        'rating': dict_city.get('rating'),
                        # 'trip_type':driver.find_element(By.XPATH,xpath + f'/div[2]/div[3]/div/span[@class="hHMDb _R Me"]').text,
                        'review_title': review_title,
                        'review':review,
                        }
                    dict_hotel_reviews.update(temp)
                    pprint(dict_hotel_reviews)
                    time.sleep(1)
                    sqlite_update(data=dict_hotel_reviews,table='reviews')
                except:
                    print("could not find {hotel_url}")

            driver.close()
            driver.quit()                
            # break
        # break
        
#==============================================================
def update_info_cities_json(input_file='cities.txt',output_file='info_cities.json'):
    my_api_key = "95175A870CB7432FA39DF1715B267E6D"
    cities = get_cities(filename = input_file)
    # location_ids= get_location_ids()
    new_cities = []
    bar_length = 48
    count = 0
    for i,c_s in enumerate(cities[301:400]):
        # print(c_s)
        time.sleep(0.02)
        temp_info_cities = str(get_tripadvisor_hotels(api_key=my_api_key, city_state = c_s))
        temp_info_cities = eval(temp_info_cities)
        new_cities.extend(temp_info_cities)
        sys.stdout.write('\r')
        sys.stdout.write(f"Completed: {c_s} |[{i} of {20}]")
    
    # review_df.to_sql(con=conn,index=True,if_exists="replace",name="info")
    # conn.close()

    with open (output_file,'r') as f:
        text= f.read()
    dict_info_cities= eval(text)
    dict_info_cities.extend(new_cities)
    json.dump(dict_info_cities,open(output_file,'w'))
    exit()

def get_dict_from_json(json_file = 'info_cities.json'):
    with open (json_file,'r') as f:
        text= f.read()
    return eval(text)

#==============================================================
if __name__ == "__main__":
    # Replace with your actual API key
    
    ### Create input json file 
    # update_info_cities_json()
    dict_info_cities = get_dict_from_json(json_file = 'info_cities.json')
    # df = pd.DataFrame.from_dict(dict_info_cities)
    # df.to_csv('blabla.csv')

    ### Create hotel info csv 
    # update_info_csv('hotels_info.csv')
    # ## Create hotel reviews csv 
    update_review_csv('hotel_reviews.csv')