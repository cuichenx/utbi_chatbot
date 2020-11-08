import urllib
import requests
from bs4 import BeautifulSoup

#text = 'difference between measure and dimension in tableau' + ' site:tableau.com'
text = 'how do i put web page in dashboard'+ ' site:tableau.com'
text = 'how do i create a chart with 2 axes' + ' site:tableau.com'
# text = 'extract summary from google scrape beautifulsoup'

def get_search_results(text, out_file=None, num_res=3):
    """
    search with google, returns result in list where each obj in list is in the format of [title,link,desc]
    """
    # specify the source website
    text += ' site:tableau.com'
    text = urllib.parse.quote_plus(text)

    url = 'https://google.com/search?q=' + text
    USER_AGENT = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
    
    # TODO: add delay here?
    response = requests.get(url,headers=USER_AGENT)

    soup = BeautifulSoup(response.text, 'html.parser')
    result_block = soup.find_all('div', attrs={'class': 'g'})

    final_result = []
    for rb_ind in range(len(result_block)):
        if len(final_result)==num_res:
            # done sraping
            break
        
        rb = result_block[rb_ind]
        # print(rb_ind)
        if rb.find('h3'):
            title = rb.find('h3').text
            link = rb.find('a', href=True)['href']

            desc = rb.find(class_='IsZvec').text
            
            if not desc:
                # print(rb_ind)
                # print("got here")
                desc = rb.find(class_='ILfuVd')
                if desc:
                    desc = desc.text
                else:
                    desc = ''
            final_result.append([title,link,desc])
            print('\n'.join([title,link,desc]))

    if out_file is not None:
        with open(out_file,"a+",encoding='utf8') as f:
            f.writelines([r + '\n' for r in search_res])
    
    return final_result
