import os
from bs4 import BeautifulSoup
import pandas


#Creating empty list for our data
data = []
#Creating empty list for the relations
relationships = []

#Loading the folder created when scraping
files = sorted(os.listdir('sinti-en-roma-namenlijst'))
#For loop that looks at each file 
for file in files:
    print('Parsing', file)
    #Loads the file
    text = open('sinti-en-roma-namenlijst/'+file,'r',encoding='utf-8').read()
    soup = BeautifulSoup(text,features='lxml')
    #Finding the block that we are intrested in
    name = soup.find('header',attrs={'class':'c-warvictim-intro'})
    #The block that contains the information needed
    person_info = name.find('p',attrs={'class':'c-warvictim-intro__sub'}).text
    person_info = person_info.strip()
    #Joining the parts with a space so its easier to extract each part
    person_info = ' '.join(person_info.split())
    #Looks at html files and takes their person ID
    pID = file.split('-')[0]
    #Looks at our html files and takes their names
    pName = file.replace(pID+'-','')
    pName = pName.replace('.html','')
    #Looks at our list of person_info and splits
    splitted = person_info.split(', ')
    #Birthplace is first
    Birthplace = splitted[0]
    #Deathdate is last
    Deathdate = splitted[2]
    #The the html birthdate and deathplace are connected by a dash, we split
    #at the first dash, because some places include a dash
    Birthdate = splitted[1].split(' – ',1)[0]
    Deathplace = splitted[1].split(' – ',1)[1]
    #Finding the age
    age = name.findAll('p',attrs={'class':'c-warvictim-intro__sub'})
    #If there are two, we take the second
    if len(age)==2:
        age = age[1].text.split(' ',4)[-1]
    else:
        age = 'Unknown'
    #Appending all our variables to the empty data list 
    data.append([pID,pName,Birthplace,Birthdate,Deathplace,Deathdate,age])

    #Most of the relation except for "other" are in this block
    family_tree = soup.findAll('div',attrs={'class':'c-warvictim-family-tree'})
    #For each type we loop
    for family in family_tree:
        relations = family.findAll('div',attrs={'class':'c-warvictim-family-tree__block'})
        for relation in relations:
            general = relation.find('h3',attrs={'class':'c-warvictim__subtitle'})
            #If there is no content in this block it contains themselves and their spouse.
            #We are only intrested in their spouse, so we mark the general type as that
            if general == None:
                general_type = 'Spouse'
            #Else we take the text content of the block and assign that as general type
            else:
                general_type = general.text
            #All the people they have relations to are in this block
            people = relation.findAll('h4',attrs={'class':'c-card-family__title'})
            #The specific relationship type is in this block
            specific = relation.findAll('div',attrs={'class':'c-card-family__relation'})
            #'people' and 'specific' are lists, therefore we loop over each item
            for i in range(len(people)):
                pID = file.split('-')[0]
                #The link for the other person icluding their ID is after 'a'
                link = people[i].find('a')
                #We get the ID
                rID = link['href'].split('/')[-2]
                #Getting the text containing the specific relationship type
                specific_type = specific[i].text.strip()
                #Because some of the text included many spaces and the word "survivor"
                specific_type = specific_type.split(' ')[0].strip()
                #If this is blank or says survivor only, we rename to 'Unknown'
                if specific_type == '' or specific_type == 'Survivor':
                    specific_type = 'Unknown'
                #If the ID's are identical we dont want them in our data
                if pID != rID:
                    relationships.append([pID,rID,general_type,specific_type])
    #'Other' family is in this block
    family_other = soup.find('div',attrs={'class':'c-warvictim-family-other'})
    #If this block is not empty, we continue
    if family_other != None:
        #Assign the general type as 'other'
        general_type = 'other'
        #Finding all the relations in the block
        people = family_other.findAll('h4',attrs={'class':'c-card-family__title'})
        for person in people:
            pID = file.split('-')[0]
            link = person.find('a')
            rID = link['href'].split('/')[-2]
            relationships.append([pID,rID,general_type,'Unknown'])

#Adding data to dataframe
df = pandas.DataFrame(data,columns = ['ID','Name','Birthplace','Birthdate',
                                      'Deathplace','Deathdate','age'])
#Saving to a csv file
df.to_csv('Victims.csv', index=False, encoding='utf-8')

df = pandas.DataFrame(relationships,columns = ['ID1','ID2','General relationship type',
                                               'Detailed relationship type'])
df.to_csv('Relationships.csv', index=False, encoding='utf-8')

