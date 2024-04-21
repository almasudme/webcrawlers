import argparse
import json
import glob
import os
import pandas as pd
import sqlite3

class JSONParser():
    def __init__(self,input_dir, output_db,**kwargs):
        self.input_dir = input_dir
        self.db = output_db
        self.df = {
            'info': pd.DataFrame(),
            'reviews':pd.DataFrame()
            }
        
        
        
    def create_info_table(self):
        print(f"Creating info table in : {self.db }")
        # dataframe
        files = glob.glob(f'{self.input_dir}/info_*.json')
        print(f'found {len(files)} files')
        
        for file in files:
            temp_df = self.load_info_from_json(file,'dataframe')

            self.df['info'] = pd.concat([self.df['info'],temp_df], ignore_index=True)
        print(f"Shape of df: {self.df['info'].shape}")            
        self.df['info'].drop_duplicates(subset=['location_id'],inplace=True)   
        print(f"Shape of df after removing duplicates.: {self.df['info'].shape}") 

        # save dataframe into a table
        conn = sqlite3.connect(self.db)
        
        self.df['info'].to_sql('info',con=conn, index=False,if_exists='append',)
        conn.close()

    def create_review_table(self):
        print(f"Creating info table in : {self.db }")
        # dataframe
        files = glob.glob(f'{self.input_dir}/reviews_*.json')
        print(f'found {len(files)} files')
        
        for file in files:
            temp_df = self.load_review_from_json(file,'dataframe')

            self.df['reviews'] = pd.concat([self.df['reviews'],temp_df], ignore_index=True)
        print(f"Shape of df: {self.df['reviews'].shape}")            
        # self.df['reviews'].drop_duplicates(subset=['location_id'],inplace=True)   
        # print(f"Shape of df after removing duplicates.: {self.df['reviews'].shape}") 

        # save dataframe into a table
        conn = sqlite3.connect(self.db)
        
        self.df['reviews'].to_sql('reviews',con=conn, index=False,if_exists='append',)
        conn.close()
    

    def load_info_from_json(self,filename,type='dict'):
        with open(filename,'r') as f:
            list_of_dict_from_file = json.load(f)
        info_dict = []    
        for dict_from_file in list_of_dict_from_file:
            temp_dict = {
            'hotel_name'     : dict_from_file.get('name'),
            'address'        : dict_from_file.get('address_obj').get('address_string'),
            'subratings'     : str(dict_from_file.get('subratings')),
            'rating'         : dict_from_file.get('rating'),
            'n_reviews'      : dict_from_file.get('num_reviews'),
            'phone_number'   : dict_from_file.get('phone'),
            'price_level'   : dict_from_file.get('price_level'),
            'ranking'        : dict_from_file.get('ranking_data',{'none':'no_rank'}).get('ranking_string'),
            'about_text'     : dict_from_file.get('description'),
            'amenities_list' : str(dict_from_file.get('amenities')),
            'contact'        : dict_from_file.get('address_obj').get('address_string'),
            'web_url'        : dict_from_file.get('web_url').replace('?m=66827',''),
            'location_id'    : dict_from_file.get('location_id'),
            'city'    : dict_from_file.get('address_obj').get('city'),
            'state'    : dict_from_file.get('address_obj').get('state'),
            'postalcode'    : dict_from_file.get('address_obj').get('postalcode'),
            'country'    : dict_from_file.get('address_obj').get('country'),
            }
            info_dict.append(temp_dict)
        ret = {
            'dict':info_dict,
            'dataframe':pd.DataFrame(info_dict)
            }
        return ret[type]
    
    def load_review_from_json(self,filename,type='dict'):
        with open(filename,'r') as f:
            list_of_dict_from_file = json.load(f)
               
        review_dict = [] 
        # print(filename)
        for dict_from_file in list_of_dict_from_file:
            
            # print(dict_from_file )
            temp_dict = {}
            if dict_from_file == 'error': break
            temp_dict['location_id']    = dict_from_file.get('location_id')
            temp_dict['id']    = dict_from_file.get('id')
            temp_dict['review']    = dict_from_file.get('text')
            temp_dict['review_title']    = dict_from_file.get('title')
            temp_dict['hotel_name']    = dict_from_file.get('name',None)
            temp_dict['rating']    = dict_from_file.get('rating')
            temp_dict['date']    = dict_from_file.get('published_date')
            temp_dict['name']    = dict_from_file.get('username')
            temp_dict['time']    = dict_from_file.get('travel_date')
            temp_dict['trip_type']    = dict_from_file.get('trip_type')
            temp_dict['time']    = dict_from_file.get('travel_date')
            temp_dict['helpful_votes']    = dict_from_file.get('helpful_votes')
            owner_response = dict_from_file.get('owner_response')
            if owner_response:
                temp_dict['response_review']    = dict_from_file.get('owner_response').get("text")
                temp_dict['responded_person']    = dict_from_file.get('owner_response').get("author")
                temp_dict['response_date']    = dict_from_file.get('owner_response').get("published_date")
            
            # print(temp_dict)
            # print("="*30)
            # print(dict_from_file)
            review_dict.append(temp_dict)
            # print(review_dict[0]['id'])
            # break
        ret = {
            'dict':review_dict,
            'dataframe':pd.DataFrame(review_dict)
            }
        return ret[type]

    def update_db_from_dict(self,db='hotel_data_from_api.db',table = None, input_list = None):
        if not input_list: return "No data provided"
        if not table:return "missing table name in input argument"
        if not db:return "missing db name in input argument"
        db_file_name = db
        conn = sqlite3.connect(db_file_name)
        
        for data in input_list:
            insert_str = f"UPDATE OR INSERT INTO {table} {str(tuple(data.keys()))} VALUES {str(tuple(data.values()))}"
            print(insert_str)
            cursor = conn.cursor()
            cursor.execute(insert_str)
            conn.commit()
            cursor.close()
        conn.close()



    def run(self):
        print(f"input directory is {self.input_dir}")        
        print(f'looking for json file in {self.input_dir}')
               
        self.create_info_table()
        self.create_review_table()

def main():
    parser = argparse.ArgumentParser(description="Process API output files to create database")
    parser.add_argument("--input_dir", action="store", help="input directory containing json")
    parser.add_argument("--output_db", action="store", help="output database name")
    args = parser.parse_args()
    input_dir = args.input_dir
    output_db = args.output_db 
    proc = JSONParser(input_dir=input_dir,output_db=output_db)
    proc.run()


if __name__ == '__main__':
    main()