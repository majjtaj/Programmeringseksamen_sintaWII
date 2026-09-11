import geopy
import pandas as pd
from geopy.exc import GeocoderTimedOut
import time
import numpy as np

#Reading our CSV
data = pd.read_csv('Victims.csv')

locator = geopy.Nominatim(user_agent="jane.doe@gmail.com")

#The column of the CSV file we want to geocode is 'Birthplace'
Birthlocations = data['Birthplace']
#Creating empty lists for longitude and latitude
Birthlatitudes = []
Birthlongitudes = []

#Looping over each place
for i in range(len(Birthlocations)):
    print("Geocoding", Birthlocations[i])
    location = None
    try:
        #Setting location
        location = locator.geocode(Birthlocations[i],timeout=10)
        #If the location can not be found
        if location == None:
            #Add them as None
            Birthlatitudes.append(np.nan)
            Birthlongitudes.append(np.nan)
        else:
            #Append coordinates if they exist
            Birthlatitudes.append(location.latitude)
            Birthlongitudes.append(location.longitude)
    except GeocoderTimedOut:
        print("Not able to geocode", Birthlocations[i])
        Birthlatitudes.append(np.nan)
        Birthlongitudes.append(np.nan)
    time.sleep(1)
    
    
Deathlocations = data['Deathplace']
Deathlatitudes = []
Deathlongitudes = []

for i in range(len(Deathlocations)):
    print("Geocoding", Deathlocations[i])
    location = None
    try:
        location = locator.geocode(Deathlocations[i],timeout=10)
        if location == None:
            Deathlatitudes.append(np.nan)
            Deathlongitudes.append(np.nan)
        else:
            Deathlatitudes.append(location.latitude)
            Deathlongitudes.append(location.longitude)
    except GeocoderTimedOut:
        print("Not able to geocode", Deathlocations[i])
        Deathlatitudes.append(np.nan)
        Deathlongitudes.append(np.nan)
    time.sleep(1)

#Making the lists into column in our dataset
data['Birthlatitude'] = Birthlatitudes
data['Birthlongitude'] = Birthlongitudes
data['Deathlatitude'] = Deathlatitudes
data['Deathlongitude'] = Deathlongitudes
#Saving the geocode columns to a new CSV file
data.to_csv('Victims_geocoded.csv', index=False, encoding='utf-8')