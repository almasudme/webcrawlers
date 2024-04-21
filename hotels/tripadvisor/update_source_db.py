import pandas as pd
import sqlite3

input_db = '/home/mir/grepo/webcrawlers/hotels/hotels_data6.db'
delta_db = 'hotel_data_from_api.db'




cnx = sqlite3.connect(input_db)
input_df = pd.read_sql_query("SELECT * FROM info6", cnx) 
cnx.commit()
cnx.close()

cnx = sqlite3.connect(delta_db)
delta_df = pd.read_sql_query("SELECT * FROM info", cnx) 
cnx.commit()
cnx.close()



output_df = pd.concat([input_df,delta_df])
print(output_df)
