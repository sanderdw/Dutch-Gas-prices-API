"""
Dutch Gas prices API Module
"""
import json
import os
import time
from io import BytesIO
import re
from PIL import Image, ImageEnhance, ImageDraw
import requests
import math
import pytesseract
from fake_headers import Headers

# Settings
# Something like lru_cache would be nice but has no time expiring support, so custom json storage
CACHE_TIME = 3600

def gas_prices(station_id, fuel = None):
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
                for value in search_value:
                    if value in line.lower():
                        word_list = line.split()
                        break
                if word_list:
                    break


            if word_list:
                return_value1 = word_list[-1].replace(',', '.')
                return_value2 = re.sub("[^0-9,.]", "", return_value1)
                if len(return_value2) == 5: #the superscript digit should not be incorporated
                    return_value2 = return_value2[:4]
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
            img2 = img.convert('L') #assign other var, convert does not work otherwise
            width, height = img2.size
            newsize = (width*2, height*2)
            img2 = img2.resize(newsize) #resize for better ocr
            draw = ImageDraw.Draw(img2)
            draw.rectangle((((width*2) - 180), 100, (width*2), 0), fill=240) #replace logo, prevent OCR from reading text
            img2.save(f'cache/{station_id}.png')
            ocr_result = pytesseract.image_to_string(img2, config='--psm 6 --oem 3') #configure tesseract explicit
            ocr_lines = ocr_result.split("\n")

            #lowercase definition of fuels to search
            euro95_prijs = _search_value(ocr_lines, ['euro 95','euro95','(e10)'])
            diesel_prijs = _search_value(ocr_lines, ['diesel','(b7)'])
            lpg_prijs = _search_value(ocr_lines, ['lpg'])
            euro98_prijs = _search_value(ocr_lines, ['euro 98','euro98','e5'])

            if (euro95_prijs is None) or (diesel_prijs is None):
                data = {
                    'station_id': station_id,
                    'euro95': euro95_prijs,
                    'euro98': euro98_prijs,
                    'diesel' : diesel_prijs,
                    'lpg' : lpg_prijs,
                    'ocr_station' : ocr_lines[0],
                    'status' : 'Station exists?'
                    }
            else:
                data = {
                    'station_id': station_id,
                    'euro95': euro95_prijs,
                    'euro98': euro98_prijs,
                    'diesel' : diesel_prijs,
                    'lpg' : lpg_prijs,
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
                'euro95': None,
                'euro98': None,
                'diesel' : None,
                'lpg' : None,
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

    #Only return the fuel that was requested
    if fuel:
        newdata = {
                'station_id': return_value['station_id'],
                'prijs': return_value[fuel],
                'ocr_station' : return_value['ocr_station'],
                'status' : return_value['status']
                }
        return_value = newdata
    print (return_value)
    return return_value

if __name__ == '__main__':
    gas_prices('00000') # Executed when this file is triggered directly
