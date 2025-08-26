from seeq import spy
from dotenv import load_dotenv
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import urllib.parse
import os
from datetime import datetime, timedelta, timezone
import time
import pickle
import re

env_path = r"C:\Users\zixiang.chen\.env"
tag_list_path = r"..\data\all_pi_tags_KS.txt"
tag_list_found_path = r"..\data\found_pi_tags_KS.csv"
tag_list_not_found_path = r"..\data\missing_pi_tags_KS.txt"



def search_tag(tag):
    try:
        search_result = spy.search({"Name": tag})
        filtered = search_result[
            (search_result["Name"] == tag)
            & (search_result["Datasource Name"] == "DSSHISTLIQ2")
        ]
 
        if filtered.empty:
            return None, tag  # No exact match found
        else:
            return filtered, None
    except Exception as e:
        print(f"Error processing tag '{tag}': {e}")
        return None, tag
    

if __name__ == "__main__":
    load_dotenv(env_path)
 
    # Login to Seeq
    spy.login(
        url=     os.getenv("TC_SEEQ_SERVER"),
        username=os.getenv("TC_SEEQ_ACCESS_KEY"),
        password=os.getenv("TC_SEEQ_ACCESS_KEY_PASSWORD"),
    )
 
    # Get Tag names from file
    with open(tag_list_path, "r") as file:
        tag_names = [line.strip() for line in file if line.strip()]
 
    all_results = []
    missing_tags = []
 
    # Use ThreadPoolExecutor for parallel searching
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(search_tag, tag) for tag in tag_names]
 
        for future in as_completed(futures):
            result, missing = future.result()
            if result is not None:
                all_results.append(result)
            if missing is not None:
                missing_tags.append(missing)
 
    # Concatenate all results into a single DataFrame
    if all_results:
        df_pi_tags = pd.concat(all_results, ignore_index=True)
        df_pi_tags.to_csv(tag_list_found_path)
        print('Found %d tags. Written to %s'%(len(df_pi_tags.index), tag_list_found_path))
    else:
        print("No tags found.")
 
    if missing_tags:
        with open(tag_list_not_found_path, 'w') as f:
            for idx, tag in enumerate(missing_tags):
                f.write(tag + "\n")
        print('Missing %d tags. Written to %s'%(idx+1, tag_list_not_found_path))