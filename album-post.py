from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.relative_locator import locate_with
import re
import json
import urllib.request
import os
import sqlite3
import csv


# selenium setup
option = webdriver.ChromeOptions()
chrome_prefs = {}
option.experimental_options["prefs"] = chrome_prefs
chrome_prefs["profile.default_content_settings"] = {"images": 2}
chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
driver = webdriver.Chrome(options=option)


# csv filename
filename = 'album_post_list.csv'

# base directory for assets
scrape_directory = 'C:/OTD'

# connect to database, create tables
conn = sqlite3.connect('album.db')
c = conn.cursor()
c.execute("""CREATE TABLE posts (post_id INTEGER, post_date TEXT, post_title TEXT, author_name TEXT, author_id TEXT, contents TEXT)""")
c.execute("""CREATE TABLE comments (comment_id INTEGER, post_id INTEGER, comment_order INTEGER, comment_author_name TEXT, comment_author_id TEXT, comment_date TEXT, comment_content TEXT, reply_level INTEGER)""")



progress_count = 1
with open(filename, 'r') as csvfile:
    datareader = csv.reader(csvfile)
    # for every post in csv
    for row in datareader:

        # fetching output fields and assets

        #POST ID
        post_id = row[1]

        url  = f'http://www.otd.kr/bbs/board.php?bo_table=album&wr_id={post_id}'
        driver.get(url)

        #POST TITLE
        post_title = driver.find_element(By.CSS_SELECTOR, "div[style='color:#505050; font-size:13px; font-weight:bold; word-break:break-all;']").text

        #POST DATE
        post_date = driver.find_element(By.CSS_SELECTOR, "span[style='color:#888888;']").text

        #AUTHOR NAME
        post_author_full = driver.find_element(locate_with(By.TAG_NAME, "a").near({By.CLASS_NAME: "member"})).get_attribute("title")
        
        author_name = post_author_full.split("]",1)[1] 
        author_id = re.search(r"\[(\w+)\]", post_author_full).group(1)

        #TEXT BODY
        contents = driver.find_element(By.CLASS_NAME, "view-img").get_attribute("innerHTML").replace('''src="http://www.otd.kr''', '''src="''').replace('''href=\"http://www.otd.kr/gn''', '''href="''')

        #IMAGES
        images_container = driver.find_element(By.CLASS_NAME, "view-img")
        images = images_container.find_elements(By.TAG_NAME, "img")
        for image in images:
            img_src = image.get_attribute("src")
            img_location = img_src.replace("http://www.otd.kr", "D:/OTD")
            basedir = os.path.dirname(img_location)
            if not os.path.exists(basedir):
                os.makedirs(basedir)
            urllib.request.urlretrieve(img_src, img_location)

        #COMMENTS
        comments = []
        comment_containers = driver.find_elements(By.XPATH, '//*[@id="commentContents"]/table')
        comment_id_containers = driver.find_elements(By.XPATH, '//*[@id="commentContents"]/a')
        comment_order = 1
        for comment_container in comment_containers:          
            comment_author_full = comment_container.find_element(By.TAG_NAME, "a").get_attribute("title")
            comment_author_name = comment_author_full.split("]",1)[1] 
            comment_author_id = re.search(r"\[(\w+)\]", comment_author_full).group(1)
            comment_contents = comment_container.find_element(By.CLASS_NAME, "comment-cont").text
            comment_date = comment_container.find_element(By.CSS_SELECTOR, "span[style='color:#888888; font-size:11px;']").text
            reply_level_container = comment_container.find_element(By.XPATH, './/tbody/tr/td[1]')
            reply_level = len(reply_level_container.find_elements(By.TAG_NAME, "div"))
            comment_id = comment_container.find_element(By.TAG_NAME, "input").get_attribute("id").replace("secret_comment_", "")
            c.execute("INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(comment_id, post_id, comment_order, comment_author_name, comment_author_id, comment_date, comment_contents, reply_level))
            comment_order += 1


#PUSH POST DATA INTO DATABASE
        c.execute("INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?)",(post_id, post_date, post_title, author_name, author_id, contents))
        conn.commit()
        print(f'Post stored: {post_id}, {progress_count}/8495')
        progress_count = progress_count + 1