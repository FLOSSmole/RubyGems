# -*- coding: utf-8 -*-
'''
This program is free software; you can redistribute it
and/or modify it under the terms of the Perl Artistic License 2.0.
Copyright (C) 2015 Megan Squire, Gavan Roth, and Evan Ashwell
We're working on this at http://flossmole.org - Come help us build 
an open and accessible repository for data and analyses for open
source projects.
If you use this code or data for preparing an academic paper please
provide a citation to 
Howison, J., Conklin, M., & Crowston, K. (2006). FLOSSmole: 
A collaborative repository for FLOSS research data and analyses. 
International Journal of Information Technology and Web Engineering, 
1(3), 17–26.
and
FLOSSmole (2004-2016) FLOSSmole: a project to provide academic access to data 
and analyses of open source projects.  Available at http://flossmole.org 
usage:
python RubyGemsProjectCollector.py <datasource_id> <password>
'''

import urllib.request
from bs4 import BeautifulSoup
import sys
import pymysql
import datetime

datasource_id = sys.argv[1]
password = sys.argv[2]

urlBase = "https://rubygems.org/gems"
countT = 1
count = 0
page = 1
i = 0

#Create arrays with letters and their corresponding number of pages
letters = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
nums = [None]*26

#Populates the nums array with the curent total number of pages of projects for each letter
while i < len(letters):
    p = urllib.request.urlopen(urlBase+"?letter=" + letters[i])
    s = BeautifulSoup(p, "lxml")
    for row in s.findAll('div', { "class" : "pagination" }):
        allTag = row.find_all('a')
        for tag in allTag:
            if countT == 10:
                nums[i] = int(tag.text)
            countT=countT+1
    i = i+1
    countT = 1

# establish database connection: ELON
try:
    db = pymysql.connect(host='grid6.cs.elon.edu',
                                  database='rubygems',
                                  user='megan',
                                  password=password,
                                  charset='utf8')
except pymysql.Error as err:
    print(err)
else:
    cursor = db.cursor()


# establish database connection: SYR      
try:
    db1 = pymysql.connect(host='flossdata.syr.edu',
                                  database='rubygems',
                                  user='megan',
                                  password=password,
                                  charset='utf8')
except pymysql.Error as err:
    print(err)
else:
    cursor1 = db1.cursor()


#outer while loop used to iterate through the 26 letters
while count < len(letters):
    letter = letters[count]
    pages = nums[count]
    
    #This while loop itterates through all the pages listing the projects of the current letter
    while page < pages+1:
        listUrl = urlBase + "?letter=" + letter +"&" 
        listUrl = listUrl + "page=%d" % page
        try:
            listPage = urllib.request.urlopen(listUrl)
        except urllib.error.URLError as e:
            print (e.reason)
        else:
            soup = BeautifulSoup(listPage, "lxml")
            print(listUrl)

        #Pulls all project names on the given list page 
        for row in soup.findAll('a', { "class" : "gems__gem" }):
            ref = row['href']
            projectName = ref[6:]
            
            #---- get RSS atom file for each project
            RSSurl = urlBase + "/" + projectName + "/versions.atom"
            try:
                RSSfile = urllib.request.urlopen(RSSurl)

            except urllib.error.URLError as e:
                print(e.reason)
            else:
                RSSsoup = BeautifulSoup(RSSfile, "lxml")
                RSSpage = RSSsoup.find('feed')
                RSSstring = str(RSSpage)
            
            #---- get HTML base page for each project
            homePageURL = urlBase + "/" + projectName
            try:
                homePageFile = urllib.request.urlopen(homePageURL)
                
            except urllib.error.URLError as e:
                print(e.reason)
         
            else:
                homePageSoup = BeautifulSoup(homePageFile, "lxml")
                homePageString = str(homePageSoup)

            #---- get HTML versions for each project            
            versionsPageURL = urlBase + "/" + projectName + "/versions"
            #little confused on how this directly obtains the version
            try:
                versionFile = urllib.request.urlopen(versionsPageURL)
            except urllib.error.URLError as e:
                print(e.reason)
            else:
                versionSoup = BeautifulSoup(versionFile, "lxml")
                versionString = str(versionSoup)
        
            
            #---- put everything in the database
            try:
                cursor.execute("INSERT IGNORE INTO rubygems_project_pages( \
                    project_name, \
                    datasource_id, \
                    rss_file, \
                    html_file, \
                    html_versions_file, \
                    last_updated) \
                     VALUES (%s,%s,%s,%s,%s,%s)", 
                     (projectName, 
                      datasource_id, 
                      RSSstring, 
                      homePageString, 
                      versionString, 
                      datetime.datetime.now()))
                db.commit()
            except pymysql.Error as err:
                print(err)
                db.rollback()     
            try:
                cursor1.execute("INSERT IGNORE INTO rubygems_project_pages( \
                    project_name, \
                    datasource_id, \
                    rss_file, \
                    html_file, \
                    html_versions_file, \
                    last_updated) \
                     VALUES (%s,%s,%s,%s,%s,%s)", 
                     (projectName, 
                      datasource_id, 
                      RSSstring, 
                      homePageString, 
                      versionString, 
                      datetime.datetime.now()))
                db1.commit()
            except pymysql.Error as err:
                print(err)
                db1.rollback()
        page = page + 1
    count = count + 1
    page = 1

cursor.close()
db.close() 
 
cursor1.close()
db1.close()  
