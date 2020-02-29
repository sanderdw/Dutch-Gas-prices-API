"""
Dutch Gas prices API Module
"""
import json
import os
import time
from io import BytesIO
import re
from PIL import Image
import requests
import pytesseract
from fake_headers import Headers

# Settings
# Something like lru_cache would be nice but has no time expiring support, so custom json storage
CACHE_TIME = 3600

def gas_prices(station_id):
    """
    Main Dutch Gas prices API Function
    """
    url = f'https://tankservice.app-it-up.com/Tankservice/v1/places/{station_id}.png'

    def _search_value(lines, search_value):
        """
        OCR logic for Euro 95 en Diesel, TODO rewrite logic, dirty as * now... & Split up....
        """
        return_value = None
        try:
            word_list = None
            for i, line in enumerate(lines):
                if search_value in line:
                    word_list = line.split()
                    break
            if word_list is None and search_value == 'Euro 95':
                for i, line in enumerate(lines):
                    if 'Euro95' in line:
                        word_list = line.split()
                        break
            else:
                return_value1 = word_list[-1].replace(',', '.')
                return_value2 = re.sub("[^0-9,.]", "", return_value1)
                return_value = float(return_value2)
                if return_value > 2:
                    return_value = float(return_value2[0] + '.' + return_value2[1])
                else:
                    pass
        except Exception as exception_info:
            print(f'_search_value failed: {exception_info}')
                
        return return_value


    def _write_stationdata(station_id):
        """
        Query the api and cache the results to a json file
        """
        headers = Headers(headers=True).generate()

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img.save(f'cache/{station_id}.png')
            ocr_result = pytesseract.image_to_string(img)
            ocr_lines = ocr_result.split("\n")

            benzine_prijs = _search_value(ocr_lines, 'Euro 95')
            diesel_prijs = _search_value(ocr_lines, 'Diesel')

            if (benzine_prijs is None) or (diesel_prijs is None):
                data = {
                    'station_id': station_id,
                    'benzine_prijs': benzine_prijs,
                    'diesel_prijs' : diesel_prijs,
                    'ocr_station' : ocr_lines[0],
                    'status' : 'Station exists?'
                    }
            else:
                data = {
                    'station_id': station_id,
                    'benzine_prijs': benzine_prijs,
                    'diesel_prijs' : diesel_prijs,
                    'ocr_station' : ocr_lines[0],
                    'status' : 'Ok'
                    }

            with open('cache/' + f'{station_id}.json', 'w') as outfile:
                json.dump(data, outfile)
        else:
            print(f'Error: statuscode: {response.status_code}')
            print(f'Error: Used header: {headers}')
            ip_addr = requests.get('https://api.ipify.org').text
            print(f'Error: Used IP: {ip_addr}')
            print(f'Error: Response text: {response.text}')
            data = {
                'station_id': None,
                'benzine_prijs': None,
                'diesel_prijs' : None,
                'ocr_station' : None,
                'status' : f'{response.status_code}'
                }
        return data


    def _read_stationdata(station_id):
        """
        Get the cached json file
        """
        with open('cache/' + f'{station_id}.json') as json_file:
            data = json.load(json_file)
            return data


    def _file_age(station_id):
        """
        Calculate the json file age
        """
        try:
            return time.time() - os.path.getmtime('cache/' + f'{station_id}.json')
        except IOError:
            return 99999999

    # Main logic
    age_of_file = _file_age(station_id)
    print(age_of_file)
    if age_of_file < CACHE_TIME:
        print('Cache request')
        return_value = _read_stationdata(station_id)
    else:
        print('New request')
        return_value = _write_stationdata(station_id)
    return return_value

if __name__ == '__main__':
    gas_prices('00000') # Executed when this file is triggered directly
