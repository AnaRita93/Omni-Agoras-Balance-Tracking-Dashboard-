#!/usr/bin/env python
# coding: utf-8

# # Omni Agoras Balance Tracking - Data Collection

# In[1]:


#pip install schedule


# In[9]:


import requests
import pandas as pd
from datetime import datetime
import hashlib
import schedule
import time
import logging

# Setup logging
logging.basicConfig(filename='extraction.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_data():
    url = "https://api.omniexplorer.info/ask.aspx?api=getpropertybalances&prop=58"
    response = requests.get(url)
    data = response.json()

    data_list = []
    for record in data:
        address = record.get('address', '')
        balance = record.get('balance', '')
        reserved = record.get('reserved', '')

        raw_id = address + balance + reserved + datetime.now().isoformat()
        id_ = hashlib.md5(raw_id.encode()).hexdigest()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        data_list.append([id_, address, balance, reserved, timestamp])
    
    df = pd.DataFrame(data_list, columns=["id", "address", "balance", "reserved", "timestamp"])
     
        # Add some logging
    logging.info('Data fetched successfully')
    
    return df

def job():
    try:
        df = fetch_data()
        # Check if the file exists
        try:
            df_existing = pd.read_csv("/home/rita/omni_agoras_app/OmniAgorasBalanceTracking/data/omni_extracted.csv")
            df = pd.concat([df_existing, df])
        except FileNotFoundError:
            pass
        df.to_csv("/home/rita/omni_agoras_app/OmniAgorasBalanceTracking/data/omni_extracted.csv", index=False)

        logging.info('Data saved to output.csv successfully')

    except Exception as e:
        logging.error('Failed to fetch and save data: {}'.format(e))

def main():
     # Run the job right away
    job()
    # Then schedule it to run every 12 hours
    schedule.every(12).hours.do(job)

    while True:
        schedule.run_pending();        time.sleep(1)
    
    #df = fetch_data()
    #df.to_csv("Documents/OmniAgorasBalanceTracking/omni_extracted.csv", index=False)

if __name__ == "__main__":
    main()


# In[ ]:




