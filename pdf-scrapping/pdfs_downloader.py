import urllib.request as request
from bs4 import BeautifulSoup
import pandas
import time
from selenium import webdriver
import glob
import os
import re
import ntpath
from random import randint
from PIL import Image
import numpy as np
from captcha_solver import CaptchaSolver
import urllib
import numpy
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, WebDriverException 
import shutil
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
import threading
import random
import argparse
import requests
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

solver = CaptchaSolver("rucaptcha", api_key='')

class SearchDOI:
    def __init__(self, folder_to_download=r"C:\Users\Maryia_Ivanina\cornell_project\pdfs_to_download",
                 folder_with_stats_to_save="../tmp",
                 file_with_urls="urls_to_download.xlsx",
                 chrome_drive_path=r"C:\chromedriver.exe",
                 on_aws=False,
                 via_urllib=False,
                 wo_selenium=False):
        print(folder_to_download)
        self.folder_to_download = folder_to_download
        self.file_with_urls = file_with_urls
        self.file_with_urls_filename = os.path.basename(self.file_with_urls)
        print(self.file_with_urls_filename)
        self.folder_with_stats_to_save = folder_with_stats_to_save
        self.via_urllib = via_urllib
        self.wo_selenium = wo_selenium

        os.makedirs(folder_to_download, exist_ok=True)
        os.makedirs(folder_with_stats_to_save, exist_ok=True)
        if not wo_selenium:
            chrome_options = webdriver.ChromeOptions()
            prefs = {"download.default_directory" : folder_to_download,
                     "download.prompt_for_download": False,
                     "download.directory_upgrade": True,
                     "safebrowsing.enabled": True}
            chrome_options.add_experimental_option("prefs",prefs)
            chrome_options.add_argument("--headless")

            if on_aws:
                self.driver = webdriver.Chrome(chrome_options=chrome_options)
            else:
                self.driver = webdriver.Chrome(executable_path=chrome_drive_path, chrome_options=chrome_options)
            self.driver.delete_all_cookies()

    def start_downloading(self):
        ## save pandas for later use 
        self.csv = pandas.read_excel(self.file_with_urls)
        
        ## place holders
        self.cov_id = int
        ## new column
        self.csv['automation_file_name'] = 'not found'
        if "href_link" not in self.csv.columns:
            self.csv['href_link'] = ''

        self.num_files_downloaded = self.num_files_dir()
    
        ##start download
        self.csv.apply(self.download, axis=1)
        
        self.csv.to_excel(os.path.join(
            self.folder_with_stats_to_save, self.file_with_urls_filename.replace('.xlsx', "_final.xlsx")))
        self.csv.to_excel(self.file_with_urls)

    def captcha_exists(self): 
        try:
            if self.driver.find_element_by_id('captcha'):
                pass
            else:
                raise ValueError('Item not found on page') 
            return True 
        except:
            return False 

    def solve_captcha(self):
        try:
            src = self.driver.find_element_by_id("captcha").get_attribute("src") ## captcha
            ## download captcha
            print(src)
            request.urlretrieve(src, "captcha.jpg")
            print("retrieved an image")

            ## slove the captcha
            solver = CaptchaSolver('rucaptcha', api_key='a8403fc353e04e924d34d41a36fa5031')
            raw_data = open('captcha.jpg', 'rb').read()
            code = solver.solve_captcha(raw_data)
            print(code)

            ##put code 
            self.driver.find_element_by_name("answer").send_keys(code)
            self.driver.find_element_by_xpath('//input[@value="Продолжить"]').click()
            
            backoff = 3
            while backoff > 0:
                time.sleep(3 * (4 - backoff))
                if(self.driver.find_elements_by_css_selector('#buttons > button')): ## download button
                    time.sleep(3)
                    self.driver.find_element_by_xpath('//*[@id="buttons"]/button').click()
                    time.sleep(6)
                    self.check_for_download()
                    backoff = 0
                else:
                    backoff -= 1
            return True
        except Exception as err:
            print(err)
            return False
        
    def rename_downloaded_file(self, cov_id):
        list_of_files = glob.glob(r"%s/*.pdf" % self.folder_to_download)
        latest_file = max(list_of_files, key=lambda x: (os.path.getctime(x), os.path.getmtime(x)))
        file_name = ntpath.basename(latest_file)
        
        updated_file_name = latest_file.replace(file_name, "{}.pdf".format(cov_id))
        shutil.move(latest_file, updated_file_name)
        
    def num_files_dir(self):
        dir_files = os.listdir(self.folder_to_download)
        return len(dir_files)
    
    def pdf_exists(self):
        try:
            self.driver.find_element_by_xpath("//a[contains(@href,'.pdf')]")
            return True 
        except NoSuchElementException:
            return False 
    
    def check_for_download(self):
        if self.num_files_dir() > self.num_files_downloaded: ## there has been a file dowloaded
            self.num_files_downloaded +=1
            self.rename_downloaded_file(self.cov_id)
            
            self.csv.loc[self.csv['id'] == self.cov_id, "automation_file_name"] = "found"
            print("Downloaded with id: ", self.cov_id)
            self.csv.to_excel(os.path.join(
                self.folder_with_stats_to_save, self.file_with_urls_filename.replace('.xlsx', "_progress.xlsx")))
            return True
        return False
            
    # watch for change in folder 
    def download_wait(self):
        seconds = 0
        dl_wait = True
        while dl_wait and seconds < 120:
            time.sleep(1)
            dl_wait = False
            for fname in os.listdir(r"%s/" % self.folder_to_download):
                if fname.endswith('.crdownload'):
                    dl_wait = True
            seconds += 1
        return True
    
    def download(self, row, backoff=2):
        while backoff > 0:
            try:
                self.download_row(row)
                backoff = 0
            except Exception as err:
                print(err)
                time.sleep(120)
                backoff -= 1

    def download_file(self, download_url, filename):
        try:
            response = urllib.request.urlopen(download_url)
            pdf_data = response.read()
            assert len(pdf_data) > 5000
            file = open(filename, 'wb')
            file.write(pdf_data)
            file.close()
            print("Downloaded file ", filename)
            self.csv.loc[self.csv['id'] == self.cov_id, "automation_file_name"] = "found"
        except Exception as err:
            print(err)

    def download_with_check(self):
        if self.download_wait():
            print("Finished waiting downloading")
            if self.check_for_download():
                print("Finished downloading")
                return True
            else:
                print("Didn't download")
        return False

    def try_download_file(self, href_link):
        if self.via_urllib:
            self.download_file(href_link, os.path.join(self.folder_to_download, "{}.pdf".format(self.cov_id)))
        else:
            self.download_with_check()
            if self.captcha_exists():
                print('captcha')
                if self.captcha_exists():
                    if self.solve_captcha():
                        print("solved captcha")
                        self.download_with_check()

    def extract_href_link(self, onclick_attribute):
        href_link = onclick_attribute.replace("location.href='", "")[:-1]
        href_link = ("https:" + href_link) if not href_link.startswith("http") else href_link
        self.csv.loc[self.csv['id'] == self.cov_id, "href_link"] = href_link
        print(href_link)
        return href_link

    def download_row(self, row):
        self.cov_id = row['id']
        sci_hub_url = "https://sci-hub.se/"
        print("Downloading: ", self.cov_id)
        if os.path.exists(os.path.join(self.folder_to_download, "{}.pdf".format(self.cov_id))):
            self.csv.loc[self.csv['id'] == self.cov_id, "automation_file_name"] = "found"
            return
        if type(row['url']) == str:
            if self.wo_selenium:
                response = requests.get(sci_hub_url + row['url'])
                response.raise_for_status()
                html_page = BeautifulSoup(response.content)
                if html_page.select("#buttons > button"):
                    onclick_attribute = html_page.select("#buttons > button")[0]["onclick"]
                    href_link = self.extract_href_link(onclick_attribute)
                    self.download_file(href_link, os.path.join(self.folder_to_download, "{}.pdf".format(self.cov_id)))
                else:
                    print("Didn't find button")
                    print(response.content)
                    response = requests.get(sci_hub_url)
                    response.raise_for_status()
                    if not response.content.strip():
                        raise ValueError("Sci-hub is blocked")
            else:
                self.driver.get(sci_hub_url);
                search_box = self.driver.find_element_by_xpath('//*[@id="input"]/form/input[2]')
                search_box.send_keys(row['url'])
                search_box.submit()
                
                if(self.driver.find_elements_by_css_selector('#buttons > button')): ## download button
                    button_save = self.driver.find_element_by_xpath('//*[@id="buttons"]/button')
                    onclick_attribute = button_save.get_attribute("onclick")
                    href_link = self.extract_href_link(onclick_attribute)
                    if not self.via_urllib:
                        button_save.click()
                        print("Clicked button")

                    self.try_download_file(href_link)
                else:
                    raise ValueError("Didn't find button")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder_to_download')
    parser.add_argument('--folder_for_urls_to_find')
    parser.add_argument('--folder_with_stats_to_save')
    parser.add_argument('--chrome_drive_path', default=r"C:\chromedriver.exe")
    parser.add_argument('--on_aws', default="False")
    parser.add_argument('--via_urllib', default="False")
    parser.add_argument('--wo_selenium', default="False")
    args = parser.parse_args()

    print("Folder to download: %s"%args.folder_to_download)
    print("Urls to find: %s"%args.folder_for_urls_to_find)
    print("Folder with stats to save: %s"%args.folder_with_stats_to_save)
    print("Chrome driver path: %s"%args.chrome_drive_path)
    print("On AWS: %s"%args.on_aws)
    print("Via urllib: %s"%args.via_urllib)
    print("Without selenium: %s"%args.wo_selenium)

    for file in os.listdir(args.folder_for_urls_to_find):
        print(file)
        filename_folder = file.split(".")[0]
        filename_folder = re.sub(r'[\\/*?:"<>|]', "", filename_folder)
        _search_doi = SearchDOI(
            folder_to_download=os.path.join(args.folder_to_download, filename_folder),
            folder_with_stats_to_save=args.folder_with_stats_to_save,
            file_with_urls=os.path.join(args.folder_for_urls_to_find, file),
            chrome_drive_path=args.chrome_drive_path,
            on_aws=args.on_aws.lower() == "true",
            via_urllib=args.via_urllib.lower() == "true",
            wo_selenium=args.wo_selenium.lower() == "true")
        _search_doi.start_downloading()