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
        load_dotenv(r"C:\Users\zixiang.chen\.env")

        self.base_url = os.getenv("SEEQ_SERVER")
        self.username = os.getenv("SEEQ_ACCESS_KEY")
        self.password = os.getenv("SEEQ_ACCESS_KEY_PASSWORD")

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
            print("Login successful")
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
            print(f"Samples for signal retrieved successfully")
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
        print(f"{self.base_url}/api/signals/{signal_id}/samples?start={from_time}&end={to_time}&period={dt}&inflate=false&boundaryValues=Outside&limit=10000000")
        response = self.session.get(
            f"{self.base_url}/api/signals/{signal_id}/samples?start={from_time}&end={to_time}&period={dt}&inflate=false&boundaryValues=Outside&limit=10000000", params=params
        )

        if response.status_code == 200:
            print(f"Samples for signal retrieved successfully")
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
    

if __name__ == "__main__":
    load_dotenv(r"C:\Users\zixiang.chen\.env")
 
    # Login to Seeq
    spy.login(
        url=os.getenv("TC_SEEQ_SERVER"),
        username=os.getenv("TC_SEEQ_ACCESS_KEY"),
        password=os.getenv("TC_SEEQ_ACCESS_KEY_PASSWORD"),
    )
 
    # Get Tag names from file
    with open("pi_tags.txt", "r") as file:
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
        print(df_pi_tags)
    else:
        print("No tags found.")
 
    if missing_tags:
        print(f"\nMissing tags: {missing_tags}")



    # Initialize the Seeq API client and authenticate
    client = SeeqAPIClient()

    # Define the payload for the API request
    signal_id = df_pi_tags.loc[2, 'ID']  # Example signal ID

    # Make a GET request to the Seeq API to retrieve signals
    response = client.get_latest_signal_sample(signal_id)

    # Print the response
    print(response)
    # Close the session
    client.close()
    
    from_time = datetime(2024, 1, 1, 7, 0, 0, tzinfo=timezone.utc)
    iso_string = from_time.isoformat()
    iso_string = iso_string.replace("+00:00", "Z")
    from_time_encoded_string = urllib.parse.quote(iso_string, safe="-T:Z")
    print(from_time_encoded_string)

    to_time = datetime(2024, 1, 2, 7, 0, 0, tzinfo=timezone.utc)
    iso_string = to_time.isoformat()
    iso_string = iso_string.replace("+00:00", "Z")
    to_time_encoded_string = urllib.parse.quote(iso_string, safe="-T:Z")
    print(to_time_encoded_string)

    # Make a GET request to the Seeq API to retrieve signals
    client = SeeqAPIClient()

    print('Try 1h:')
    response = client.get_time_series(signal_id, from_time_encoded_string, to_time_encoded_string, '1h')
    print('# of timestamps: %d | # of elements in response: %d | ratio: %f' %(24, len(response['samples']), len(response['samples'])/24))
    
    print('Try 60s:')
    response = client.get_time_series(signal_id, from_time_encoded_string, to_time_encoded_string, '60s')
    print('# of timestamps: %d | # of elements in response: %d | ratio: %f' %(24*60, len(response['samples']), len(response['samples'])/(24*60)))

    print('Try 5s:')
    response = client.get_time_series(signal_id, from_time_encoded_string, to_time_encoded_string, '5s')
    print('# of timestamps: %d | # of elements in response: %d | ratio: %f' %(24*60*12, len(response['samples']), len(response['samples'])/(24*60*12)))

    print('')
    print('Trying for 1 day of data sampled at 5s:')
    for idx in range(10):
        ID = df_pi_tags.loc[idx, 'ID']
        print('Getting data for %s'%(df_pi_tags.loc[idx, 'Name']))
        print(ID)
        start_time = time.time()
        
        response = client.get_time_series(ID, from_time_encoded_string, to_time_encoded_string, '1h')

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed time: {elapsed_time:.3f} seconds for {len(response['samples'])} sample points.")
        print('')


    print('Trying for 30 days of data sampled at 5s:')
    to_time = datetime(2024, 2, 1, 7, 0, 0, tzinfo=timezone.utc)
    iso_string = to_time.isoformat()
    iso_string = iso_string.replace("+00:00", "Z")
    to_time_encoded_string = urllib.parse.quote(iso_string, safe="-T:Z")
    data = {}
    for idx in range(100):
        seeq_ID = df_pi_tags.loc[idx, 'ID']
        pi_tag = df_pi_tags.loc[idx, 'Name']
        print('Getting data for %s | %s'%(pi_tag, seeq_ID))
        start_time = time.time()
        
        response = client.get_time_series(seeq_ID, from_time_encoded_string, to_time_encoded_string, '5s')

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed time: {elapsed_time:.3f} seconds for {len(response['samples'])} sample points.")
        print('')
        data[pi_tag] = response['samples']


    # Close the session
    client.close()

    with open('data_2024.pkl', 'wb') as file:
         pickle.dump(data, file)