from bs4 import BeautifulSoup
from bs4 import Tag, NavigableString
from selenium import webdriver
from scraping import wait

QUERY = 'how to add filter'
SEARCH_URL = 'https://www.tableau.com/search#t=support'
OUT_FILE = "tableau_kb_search_test.txt"

from selenium.webdriver.firefox.options import Options
options = Options()
options.add_argument("--headless")


def get_search_results(URL, out_file=None, num_res=3):
    # driver = webdriver.Firefox(executable_path=r"D:\geckodriver-v0.27.0-win64\geckodriver.exe")
    driver = webdriver.Firefox(executable_path="/home/cuichenx/Tools/geckodriver", firefox_options=options)
    driver.get(URL)
    wait(1, driver)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    #print(soup.prettify())
    results = soup.find_all('a', class_='CoveoResultLink')

    search_res = []
    for res in results:
        if len(search_res) == num_res:
            break
        res_url = res['href']
        res_title = res.text
        if res_url in [search_res[i][1] for i in range(len(search_res))]:  # repeated entry in search results
            continue
        search_res.append((res_title, res_url))
        print(res_title, res_url)

    if out_file is not None:
        with open(out_file,"a+",encoding='utf8') as f:
            f.writelines([r + '\n' for r in search_res])

    print(f"\nDONE!!! {len(search_res)//2} search results scraped\nOutput is stored at {out_file}")
    return search_res

def get_query_url(search_url, query, out_file=None):
    query_url = search_url.replace('#', "#q=" + query + "&")
    if out_file:
        with open(out_file,"w",encoding='utf8') as f:
            f.write(query + '\n')
            f.write(query_url + '\n')
    return query_url


def main():
    query_url = get_query_url(SEARCH_URL, QUERY, OUT_FILE)
    print(query_url)
    get_search_results(query_url, OUT_FILE)


if __name__=='__main__':
    main()