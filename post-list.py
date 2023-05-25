from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.relative_locator import locate_with
import csv
import time
from csv import DictReader

driver = webdriver.Chrome()


# number of pages for each site sections
boards_page_lims = {
    #"album": "708",
    "c_notice": "6",
    "board1": "1984",
    "pds": "25",
    "product_news": "24",
    "review": "7",
    "market_info": "36",
    "f3": "2",
    "f8": "5",
    "TT": "18",
    "FAQ": "1",
    "qa": "229",
    "di_sadnova": "25",
    "di_tourdeotd": "71",
    "di_zerorock": "6",
    "blind_drunk": "6",
    "di_bebuts": "25",
    "di_ppomppu": "33",
    "f1": "1"
}


# open login page, wait for manual login
driver.get('http://www.otd.kr/bbs/login.php')
time.sleep(15)

# filename for saving list
filename = 'post_list.csv'

# filename.csv will store the board name and post ID of every post
with open(filename, 'a', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)
    for board, page_limit in boards_page_lims.items():
        # iterating through every page, from the last page to the first
        for page_count in range(int(page_limit), 0, -1):
            # standard URL format
            url = f'http://www.otd.kr/bbs/board.php?bo_table={board}&page={page_count}'
            driver.get(url)

            link_containers = driver.find_elements(By.XPATH, '//*[@class="bg1" or @class="bg0"]')
            for link_container in link_containers:

                # detect admin-only pages, skip them
                if 'icon_secret.gif' in link_container.get_attribute('innerHTML'):
                    print("Locked topic skipped!")
                    lock_count = lock_count + 1
                    continue

                # detect pinned posts which are displayed on every page, skip them to avoid unnecessary repetition
                if '<span class="notice">' in link_container.get_attribute('innerHTML'):
                    print("Pin skipped!")
                    pin_count = pin_count + 1
                    continue
                
                # grab link to post
                post_link = link_container.find_element(By.XPATH, ".//td[2]/nobr/a[1]").get_attribute("href")
                # extract post ID from link
                start = post_link.find("&wr_id=") + len("&wr_id=")
                end = post_link.find("&page=")
                post_id = post_link[start:end]
                # output
                output = [board,post_id]
                writer.writerow(output)
                print(f'Link stored: {board},{post_id}')
