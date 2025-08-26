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
import multiprocessing

env_path = r"C:\Users\zixiang.chen\.env"
rtu_file_path = r"..\data\test.rtu"
tag_list_found_path = r"..\data\found_pi_tags_KS.csv"
from_time = datetime(2025, 1, 1, 7, 0, 0, tzinfo=timezone.utc)
to_time = datetime(2025, 7, 31, 7, 0, 0, tzinfo=timezone.utc)
deltaT = '60s'

class SeeqAPIClient:
    def __init__(self):
        """Initialize the Seeq API client by storing the base URL, username, and password from environment variables.
        This method also sets up a session for making authenticated requests to the Seeq API.

        Args:
            None
        Returns:
            None
        Raises:
            ValueError: If any of the required environment variables are not set.
        """
        load_dotenv(env_path)

        self.base_url = os.getenv("TC_SEEQ_SERVER")
        self.username = os.getenv("TC_SEEQ_ACCESS_KEY")
        self.password = os.getenv("TC_SEEQ_ACCESS_KEY_PASSWORD")

        # Check if all required environment variables are set
        if not all([self.base_url, self.username, self.password]):
            raise ValueError(
                "SEEQ_BASE_URL, SEEQ_USERNAME, and SEEQ_PASSWORD must be set in environment variables."
            )

        # Initialize the session and authenticate
        self.session = requests.Session()
        self._login()

        # Update session headers with authentication token
        self.session.headers.update(self.get_headers())

    def _login(self):
        """Authenticate with the Seeq API and store the authentication token.

        Args:
            None
        Returns:
            None
        Raises:
            Exception: If the login fails or if the authentication token is not found.
        """
        login_url = f"{self.base_url}/api/auth/login"

        self.session.headers = {
            "accept": "application/vnd.seeq.v1+json",
            "Content-Type": "application/vnd.seeq.v1+json",
        }

        payload = {"username": self.username, "password": self.password}

        response = self.session.post(
            login_url, json=payload, headers=self.session.headers
        )

        if response.status_code == 200:
            self.auth_token = response.headers.get("x-sq-auth")
            if not self.auth_token:
                # If the token is not found, raise an exception
                raise Exception("Login succeeded, but no x-sq-auth token found!")
            #print("Login successful")
        else:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")

    def get_session(self):
        """Get the authenticated session for making requests to the Seeq API.

        Args:
            None
        Returns:
            requests.Session: The authenticated session object.
        Raises:
            None
        """
        return self.session

    def get_headers(self):
        """Get the headers required for making requests to the Seeq API.

        Args:
            None
        Returns:
            dict: A dictionary containing the headers for the Seeq API requests.
        Raises:
            None
        """
        return {
            "accept": "application/vnd.seeq.v1+json",
            "Content-Type": "application/vnd.seeq.v1+json",
            "x-sq-auth": self.auth_token,
        }

    def get_latest_signal_sample(
        self, signal_id, key=datetime.now().isoformat() + "Z", lookup="AtOrBefore"
    ):
        """Retrieve samples for a specific signal by its ID from the Seeq API.

        Args:
            signal_id (str): The ID of the signal to retrieve samples for.
            key (str): The key for the sample, default is the current time in ISO format.
            lookup (str): The lookup method for the sample, default is "AtOrBefore".
        Returns:
            Returns the value of the latest sample for the specified signal.
        Raises:
            Exception: If the request fails or if the response does not contain the expected data.
        """
        params = {
            "lookup": lookup,
        }

        response = self.session.get(
            f"{self.base_url}/api/signals/{signal_id}/sample/{key}", params=params
        )

        if response.status_code == 200:
            #print(f"Samples for signal retrieved successfully")
            return response.json()["sample"]["value"]
        else:
            raise Exception(
                f"Failed to retrieve samples for signal: {response.status_code} - {response.text}"
            )
        

    def get_time_series(
        self, signal_id, from_time, to_time, dt, lookup="AtOrBefore"
    ):
        """Retrieve samples for a specific signal by its ID from the Seeq API.

        Args:
            signal_id (str): The ID of the signal to retrieve samples for.
            key (str): The key for the sample, default is the current time in ISO format.
            lookup (str): The lookup method for the sample, default is "AtOrBefore".
        Returns:
            Returns the value of the latest sample for the specified signal.
        Raises:
            Exception: If the request fails or if the response does not contain the expected data.
        """
        params = {
            "lookup": lookup,
        }
        print(f"{self.base_url}/api/signals/{signal_id}/samples?start={from_time}&end={to_time}&period={dt}&inflate=false&boundaryValues=Outside&limit=1000000")
        response = self.session.get(
            f"{self.base_url}/api/signals/{signal_id}/samples?start={from_time}&end={to_time}&period={dt}&inflate=false&boundaryValues=Outside&limit=1000000", params=params
        )

        if response.status_code == 200:
            #print(f"Samples for signal retrieved successfully")
            return response.json()
        else:
            raise Exception(
                f"Failed to retrieve samples for signal: {response.status_code} - {response.text}"
            )

    def close(self):
        """Close the session when done.

        Args:
            None
        Returns:
            None
        Raises:
            None
        """
        self.session.close()
        print("Session closed")


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
    
def encode_time(dt):
    iso = dt.isoformat().replace("+00:00", "Z")
    return urllib.parse.quote(iso, safe="-TZ")  # exclude ':' from safe characters


def fetch_data(idx, df_pi_tags, from_time_encoded_string, to_time_encoded_string, deltaT):
    client = SeeqAPIClient()  # Create a new client instance per process for safety
    
    seeq_ID = df_pi_tags.loc[idx, 'ID']
    pi_tag = df_pi_tags.loc[idx, 'Name']
    print('Getting data for %s | %s' % (pi_tag, seeq_ID))
    start_time = time.time()
    
    response = client.get_time_series(seeq_ID, from_time_encoded_string, to_time_encoded_string, deltaT)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.3f} seconds for {len(response['samples'])} sample points.")
    print('')
    
    timestamps = []
    values = []
    for item in response['samples']:
        assert 'key' in item.keys(), '"key" not found in %s' % (item)
        timestamps.append(item['key'])
        if 'value' not in item.keys():
            values.append(int(-9999))
        else:
            if response['valueUnitOfMeasure'] == 'string':
                integer = re.findall(r'\d+', item['value'])
                if len(integer) > 1:
                    raise ValueError('Expected one integer but found %d' % (len(integer)))
                else:
                    values.append(integer[0])
            else:
                values.append(item['value'])
    datetime_index = pd.to_datetime(timestamps)
    df = pd.DataFrame(values, columns=['values'], index=datetime_index)
    
    return pi_tag, df


if __name__ == "__main__":
    load_dotenv(env_path)
 
    # Login to Seeq
    spy.login(
        url=     os.getenv("TC_SEEQ_SERVER"),
        username=os.getenv("TC_SEEQ_ACCESS_KEY"),
        password=os.getenv("TC_SEEQ_ACCESS_KEY_PASSWORD"),
    )
 
    df_pi_tags = pd.read_csv(tag_list_found_path)
    
    from_time_encoded_string = encode_time(from_time)
    to_time_encoded_string = encode_time(to_time)

    
    print('Getting data from %s to %s with a %s interval'%(from_time_encoded_string, to_time_encoded_string, deltaT))

    # Make a GET request to the Seeq API to retrieve signals
    client = SeeqAPIClient()

    data = {}
    indices = range(100)
    overall_start_time = time.time()
#    with multiprocessing.Pool(processes=10) as pool:  # Adjust processes as needed, e.g., 10 for rate limits
#        results = pool.starmap(fetch_data, [(idx, df_pi_tags, from_time_encoded_string, to_time_encoded_string, deltaT) for idx in indices])
#        
#        for pi_tag, df in results:
#            data[pi_tag] = df
#    overall_end_time = time.time()
#    overall_elapsed_time = overall_end_time - overall_start_time
#    print(f"Total elapsed time for multiprocessing: {overall_elapsed_time:.3f} seconds")

    for idx in indices:
        seeq_ID = df_pi_tags.loc[idx, 'ID']
        pi_tag = df_pi_tags.loc[idx, 'Name']
        print('Getting data for %s | %s'%(pi_tag, seeq_ID))
        start_time = time.time()
        
        response = client.get_time_series(seeq_ID, from_time_encoded_string, to_time_encoded_string, deltaT)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed time: {elapsed_time:.3f} seconds for {len(response['samples'])} sample points.")
        print('')
        
        timestamps = []
        values = []
        for item in response['samples']:
            assert 'key' in item.keys(), '"key" not found in %s'%(item)
            timestamps.append(item['key'])
            if 'value' not in item.keys():
                values.append(int(-9999))
            else:
                if response['valueUnitOfMeasure'] == 'string':
                    integer = re.findall(r'\d+', item['value'])
                    if len(integer)>1:
                        raise(ValueError('Expected one integer but found %d'%(len(integer))))
                    else:
                        values.append(integer[0])
                else:
                    values.append(item['value'])
        datetime_index = pd.to_datetime(timestamps)
        data[pi_tag] = pd.DataFrame(values, columns=['values'], index=datetime_index)

    overall_end_time = time.time()
    overall_elapsed_time = overall_end_time - overall_start_time
    print(f"Total elapsed time for multiprocessing: {overall_elapsed_time:.3f} seconds")

    # Close the session
    client.close()

    print('Converting data to generate input file for rtugen...')
    for pi_tag in data.keys():
        data[pi_tag].insert(0,'tag_name',[pi_tag]*len(data[pi_tag]))
        data[pi_tag].insert(2,'quality',['GOOD']*len(data[pi_tag]))
        data[pi_tag].loc[data[pi_tag]['values']==int(-9999),'quality'] = 'BAD'
        data[pi_tag].index = data[pi_tag].index.tz_convert('MST').tz_localize(None)
    
    df = pd.concat([data[key] for key in data.keys()])
    df.insert(0,'date_string', df.index.strftime('%Y/%m/%d'))
    df.insert(1,'time_string', df.index.strftime('%H:%M:%S'))
    df.sort_index(inplace=True)
    print('Saving rtugen input file to %s...'%(rtu_file_path))
    df.to_csv(rtu_file_path, index=False, header=False, sep=" ")
    print('DONE.')

