import requests
from bs4 import BeautifulSoup
from bs4 import Tag, NavigableString
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


def wait(t, driver):
    timeout = t
    try:
        element_present = EC.presence_of_element_located((By.ID, 'main'))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load")
    finally:
        print("Page loaded\n")


def get_question_titles(URL, out_file, more_pages=10):
    driver = webdriver.Firefox(executable_path=r"D:\geckodriver-v0.27.0-win64\geckodriver.exe")
    driver.get(URL)
    wait(2, driver)
    for i in range(more_pages):
        try:
            driver.find_element_by_xpath("//button[@title='View More Posts']").click()
            wait(2.5, driver)
        except:
            wait(20, driver)
            break

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    #print(soup.prettify())
    results = soup.find_all('div', class_='cuf-questionTitle')

    question_titles = []
    for res in results:
        q_title = res.find('span').contents
        q_title = " ".join([elem for elem in q_title if isinstance(elem, NavigableString)])
        question_titles.append(q_title)
        print(q_title)

    with open(out_file,"w",encoding='utf8') as f:
        f.writelines([q+'\n' for q in question_titles])

    print(f"\nDONE!!! {len(question_titles)} question titles scraped\nOutput is stored at {out_file}")

def main():
    #url1 = 'https://community.tableau.com/s/topic/0TO4T000000QT6nWAG/tableau-server'
    #get_question_titles(url1, "tableau_server_questions2.txt", 500)
    url2 = 'https://community.tableau.com/s/topic/0TO4T000000QF8tWAG/using-tableau'
    get_question_titles(url2, "using_tableau_questions.txt", 500)


if __name__=='__main__':
    main()