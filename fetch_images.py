from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_recaptcha_solver import RecaptchaSolver
import urllib.parse
import requests
from PIL import Image
from io import BytesIO
import os
import uuid
import time
import json
from tqdm import tqdm


driver = None
characters = []
solver = None

def search(character, copyright):
    global driver
    character = character.replace(f"({copyright})", "").strip()
    copyright = copyright.replace("(series)", "").strip()

    query = f"{character} {copyright} -figure"
    query = urllib.parse.quote(query)

    url = f"https://www.google.com/search?q={query}&udm=2"
    driver.get(url)
    time.sleep(1)

def downloadImage(hash, fast=False):
    elem = driver.find_element(By.ID, 'search')
    elem = elem.find_element(By.CLASS_NAME, 'YQ4gaf')
    elem.click()
    if not fast:
        time.sleep(1)
    imgelem = driver.find_element(By.CLASS_NAME, 'FyHeAf')
    src = imgelem.get_attribute('src')
    print(src)

    if not os.path.exists("images"):
        os.makedirs("images")

    response = requests.get(src, headers={'User-Agent': 'Googlebot-Image'}, timeout=10)
    img = Image.open(BytesIO(response.content))

    img.thumbnail((720, 720))
    img.save(f'images/{hash}.webp', 'webp', quality=90, optimize=True)

def download(index, retry=0):
    global characters
    global solver
    character = characters[index]

    if retry > 3:
        print(f"Failed to download image for {characters[index]['name']} after 3 attempts.")
        return
    try:
        search(character['name'], character['copyright'][0][0])
        downloadImage(character['hash'], retry >= 1)
    except:
        print(f"Error downloading image for {character['name']}")
        try:
            recaptcha_iframe = driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')
            solver.click_recaptcha_v2(iframe=recaptcha_iframe)
        except:
            pass

        time.sleep(2)
        download(index, retry=retry + 1)
        

def main():
    global characters
    global driver
    global solver

    with open("characters.json", "r") as f:
        characters = json.load(f)

    options = webdriver.ChromeOptions() 
    options.add_argument("start-maximized")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(options=options)
    solver = RecaptchaSolver(driver=driver)

    search("NSFW", "")
    time.sleep(5)

    for i in tqdm(range(0, len(characters))):
        if characters[i]['copyright'] == []:
            continue

        if os.path.exists(f'images/{characters[i]["hash"]}.webp'):
            continue

        print(f"Character count: {characters[i]['count']}")
        print(f"Progress: {i + 1}/{len(characters)}")
        download(i)
    
    driver.quit()


if __name__ == "__main__":
    main()