import os
import sys
import logging
import json
import requests
import datetime
from msal import ConfidentialClientApplication

# Reusable function to create a logging mechanism
def create_logger(logfile=None):

    # Create a logging handler that will write to stdout and optionally to a log file
    stdout_handler = logging.StreamHandler(sys.stdout)
    try:
        if logfile != None:
            file_handler = logging.FileHandler(filename=logfile)
            handlers = [file_handler, stdout_handler]
        else:
            handlers = [stdout_handler]
    except:
        handlers = [stdout_handler]
        logging.error('Log file could not be created. Error: ', exc_info=True)

    # Configure logging mechanism
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

# Reusable function to obtain an access token
def get_token(resource):
    client = ConfidentialClientApplication(
        client_id=os.getenv('CLIENT_ID'),
        client_credential=os.getenv('CLIENT_SECRET'),
        authority='https://login.microsoftonline.com/' +
        os.getenv('TENANT_NAME')
    )
    logging.info('Issuing request to obtain access token...')
    response = client.acquire_token_for_client(resource)
    if "token_type" in response:
        logging.info('Access token obtained successfully.')
        return response['access_token']
    else:
        logging.error('Error obtaining access token')
        logging.error(response['error'] + ': ' + response['error_description'])

# Query Azure REST API
def rest_api_request(url, token, query_params=None):
    try:
        # Create authorization header
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {0}'.format(token)}

        # Issue request to Azure API
        logging.info(f"Issuing request to {url}")
        response = requests.get(
            headers=headers,
            url=url,
            params=query_params
        )

        # Validate and process response
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            logging.error('Error encountered querying Azure API')
            logging.error(
                f"Error code was: {(json.loads(response.text))['code']}")
            logging.error(
                f"Error message was: {(json.loads(response.text))['message']}")
            raise Exception
    except Exception:
        return json.loads(response.text)


def main():
    # Create logging mechanism
    create_logger()

    # Obtain an access token to Azure REST API
    token = get_token(
        resource="https://management.core.windows.net//.default"
    )

    # Create date/time stamps and filter
    todaydate = (datetime.datetime.now() +
                 datetime.timedelta(days=int(2))).strftime("%Y-%m-%d")
    startdate = (datetime.datetime.today() -
                 datetime.timedelta(days=int(os.getenv('DAYS')))).strftime("%Y-%m-%d")
    filter = "eventTimestamp ge " + startdate + " and eventTimestamp le " + \
        todaydate + " and eventChannels eq 'Admin,Operation'" #and resourceProvider eq 'Microsoft.Authorization'"

    # Get first set of tenant activity logs and write to a file
    response = rest_api_request(
        url="https://management.azure.com/providers/Microsoft.Insights/eventtypes/management/values",
        token=token,
        query_params={
            'api-version': '2015-04-01',
            '$filter': filter
        }
    )

    # Create a new file and get it formatted for an array of json objects
    logging.info('Creating output file...')
    try:
        with open('logs.json', 'w') as log_file:
            log_file.write('[')
    except Exception:
        logging.error('Output file could not be created. Error: ', exc_info=True)


    # Iterate through each returned log and write it the file
    logging.info('Adding entries to output file...')
    try:
        with open('logs.json', 'a') as log_file:
            for log_entry in response['value']:
                log_file.write(json.dumps(log_entry) + ',')
    except Exception:
        logging.error('Unable to append to log file. Error: ', exc_info=True)

    # If paged results are returned, retreive them and write to a file
    while 'nextLink' in response:
        logging.info(
            f"Paged results returned. Retrieveing from {response['nextLink']}")
        response = rest_api_request(
            url=response['nextLink'],
            token=token,
            query_params={
            }
        )
        try:
            with open('logs.json', 'a') as log_file:
                for log_entry in response['value']:
                    log_file.write(json.dumps(log_entry) + ',')
        except Exception:
            logging.error('Unable to append to log file. Error: ', exc_info=True)

    # Remove the trailing comma from the file
    try:
        logging.info('Formatting output file...')
        with open('logs.json', 'rb+') as log_file:
            log_file.seek(-1, os.SEEK_END)
            log_file.truncate()

        # Close out the array
        with open('logs.json', 'a') as log_file:
            log_file.write(']')
        logging.info('Output file created successfully.') 
    except Exception:
            logging.error('Unable to format output file. Error: ', exc_info=True)

if __name__ == "__main__":
    main()