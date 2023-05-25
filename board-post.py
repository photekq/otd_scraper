from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.relative_locator import locate_with
import re
import json
import urllib.request
import os
import sqlite3
import csv
import time
from csv import DictReader

# selenium setup
option = webdriver.ChromeOptions()
chrome_prefs = {}
option.experimental_options["prefs"] = chrome_prefs
# disable loading images in-browser
chrome_prefs["profile.default_content_settings"] = {"images": 2}
chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
driver = webdriver.Chrome(options=option)


# open login page, wait for manual login
driver.get('http://www.otd.kr/bbs/login.php')
time.sleep(15)




# csv filename
filename = 'album_post_list.csv'

# base directory for assets
scrape_directory = 'C:/OTD'

# connect to database, create tables
conn = sqlite3.connect('board.db')
c = conn.cursor()
c.execute("""CREATE TABLE posts (board TEXT, post_id INTEGER, post_date TEXT, post_title TEXT, author_name TEXT, author_id TEXT, contents TEXT, attachments_list TEXT)""")
c.execute("""CREATE TABLE comments (board TEXT, post_id INTEGER, comment_id INTEGER, comment_order INTEGER, comment_author_name TEXT, comment_author_id TEXT, comment_date TEXT, comment_content TEXT, reply_level INTEGER)""")



progress_count = 1
with open(filename, 'r') as csvfile:
    datareader = csv.reader(csvfile)
    # for every post in csv
    for row in datareader:

        # fetching output fields and assets

        #BOARD AND POST ID
        board = row[0]
        post_id = row[1]

        # standard URL format
        url  = f'http://www.otd.kr/bbs/board.php?bo_table={board}&wr_id={post_id}'
        driver.get(url)

        # FOR SAFETY ONLY # check for admin post, in case of an exception to rule in post-list scraper
        if driver.find_element(By.NAME, "fboardpassword"):
            continue

        #POST TITLE
        post_title = driver.find_element(By.CSS_SELECTOR, "div[style='color:#505050; font-size:13px; font-weight:bold; word-break:break-all;']").text

        #POST DATE
        post_date = driver.find_element(By.CSS_SELECTOR, "span[style='color:#888888;']").text

        #AUTHOR NAME     
        post_author_full = driver.find_element(By.XPATH, '//*[@id="content"]/table[1]/tbody/tr/td/table[1]/tbody/tr[1]/td/div[1]/a').get_attribute("title")
        author_name = post_author_full.split("]",1)[1] 
        author_id = re.search(r"\[(\w+)\]", post_author_full).group(1)

        #TEXT BODY
        contents = driver.find_element(By.CLASS_NAME, "view-img").get_attribute("innerHTML").replace('''src="http://www.otd.kr''', '''src="''').replace('''href="http://www.otd.kr''', '''href="''')

        #IMAGES
        images_container = driver.find_element(By.CLASS_NAME, "view-img")
        images = images_container.find_elements(By.TAG_NAME, "img")
        # expected URLs, used when detecting external assets
        typical = "http://www.otd.kr"
        rarity = "http://otd.kr"
        for image in images:
            img_src = image.get_attribute("src")
            # checking for invalid <img> tags with no src
            if not img_src:
                continue
            else:
                pass

            # if asset is from otd.kr
            if typical in img_src:
                img_location = img_src.replace(typical, scrape_directory)
            elif rarity in img_src:
                img_location = img_src.replace(rarity, scrape_directory)
            # if asset is external, place in /external/ folder
            else:
                img_location = img_src.rsplit('/', 1)[1]
                img_placeholder = "/external/" + post_id + " - " + img_location
                img_location = scrape_directory + img_placeholder
                contents = contents.replace(img_src, img_placeholder)

            # saving asset
            basedir = os.path.dirname(img_location)
            if not os.path.exists(basedir):
                os.makedirs(basedir)
            try:
                urllib.request.urlretrieve(img_src, img_location)
            except Exception:
                print("Dead image skipped")
                print(Exception)

        #ATTACHMENTS - assets not included in text body
        #attachments can show up in two ways - links, and attachment links
        links_and_attachments_container = driver.find_element(By.XPATH, '//*[@id="content"]/table[1]/tbody/tr/td/table[1]/tbody') 
        link_counter = len(links_and_attachments_container.find_elements(By.CSS_SELECTOR, "img[src='../skin/board/basic/img/icon_link.gif']"))
        attachment_counter = len(links_and_attachments_container.find_elements(By.CSS_SELECTOR, "img[src='../skin/board/basic/img/icon_file.gif']"))
        total_counter = link_counter +  attachment_counter
        attachments_range = range(2, total_counter+2)
        attachments_list = ""

        # for every possible attachment, click the link to download the attachment,
        # add attachment name to attachments_list,
        # then remove the extra comma at the end
        for n in attachments_range:
            if attachment_counter == 0:
                break
            else:
                attachment_XPATH = f'//*[@id="content"]/table[1]/tbody/tr/td/table[1]/tbody/tr[{n}]/td/a'
                attachment_container = links_and_attachments_container.find_element(By.XPATH, attachment_XPATH)
                attachment_raw = attachment_container.get_attribute("href")
                if "javascript:file_download('./" in attachment_raw:
                    attachment_mid = attachment_raw.replace("javascript:file_download('./", "")
                    attachment_link, sep, attachment_name = attachment_mid.partition(',')
                    attachment_name = urllib.parse.unquote(attachment_name[6:len(attachment_name)-5])
                    attachment_container.click()
                    time.sleep(2)
                    attachments_list += f'{attachment_name}/'
                    while any([filename.endswith(".crdownload") for filename in os.listdir("C:/Users/Administrator/Downloads/")]):
                        time.sleep(2)
                        print('File is downloading! Waiting for 2 seconds.')
                else:
                    continue
        attachments_list = attachments_list[:len(attachments_list)-1]


        #COMMENTS
        comments = []
        # find comment containers
        comment_containers = driver.find_elements(By.XPATH, '//*[@id="commentContents"]/table')
        # comment_order keeps track of the order they're shown on the page
        comment_order = 1
        for comment_container in comment_containers:          
            comment_author_full = comment_container.find_element(By.TAG_NAME, "a").get_attribute("title")
            comment_author_name = comment_author_full.split("]",1)[1] 
            comment_author_id = re.search(r"\[(\w+)\]", comment_author_full).group(1)
            comment_contents = comment_container.find_element(By.CLASS_NAME, "comment-cont").text
            comment_date = comment_container.find_element(By.CSS_SELECTOR, "span[style='color:#888888; font-size:11px;']").text
            # reply_level = 0 is a regular comment, = 1 is a reply, = 2 is a reply to a reply, etc.
            reply_level_container = comment_container.find_element(By.XPATH, './/tbody/tr/td[1]')
            reply_level = len(reply_level_container.find_elements(By.TAG_NAME, "div"))
            comment_id = comment_container.find_element(By.TAG_NAME, "input").get_attribute("id").replace("secret_comment_", "")
            c.execute("INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",(board, post_id, comment_id, comment_order, comment_author_name, comment_author_id, comment_date, comment_contents, reply_level))
            comment_order += 1


#PUSH POST DATA INTO DATABASE
        c.execute("INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(board, post_id, post_date, post_title, author_name, author_id, contents, attachments_list))
        conn.commit()
        print(f'Post stored: {post_id}, {progress_count}/53360')
        progress_count = progress_count + 1
