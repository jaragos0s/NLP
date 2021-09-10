import sys, os
import requests
import selenium
from selenium import webdriver
import requests
import pandas as pd
from pandas import DataFrame
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time
from tqdm import tqdm
import itertools


# TODO:
# save while crawling


def crawling_title(url, header):
    req = requests.get(url, headers = header)
    req.encoding = None
    soup = BeautifulSoup(req.text, 'html.parser')
    
    txt = soup.find('h3', {'id':'articleTitle'})
    if not txt:
        txt = soup.find('h4', {'class' : 'title'})
    
    if not txt:
        txt = soup.find('h2', {'class' : 'end_tit'})
    txt = txt.text
    return txt.replace('\n','').replace('\r','').replace('<br>','').replace('\t','')


def crawling_main_text(url, header):
    req = requests.get(url, headers = header)
    req.encoding = None
    soup = BeautifulSoup(req.text, 'html.parser')
    
    txt = soup.find('div', {'id':'articleBodyContents'})
    if not txt:
        txt = soup.find('div', {'id' : 'newsEndContents'})
    
    if not txt:
        txt = soup.find('div', {'id' : 'articeBody'})
    
    if not txt:
        return None
    txt = txt.text
    # txt = txt.replace('[뉴스투데이]', '').replace('[뉴스데스크]','').replace('동영상 뉴스', '').replace('[앵커]', '').replace('◀ 앵커 ▶', '').replace('[기자]', '').replace('◀ 리포트 ▶', '').replace('<앵커>', '').replace('<기자>', '').replace('<기자 멘트>','').replace('<인터뷰>', '').replace('<녹취>','')
    return txt.replace('\n','').replace('\r','').replace('<br>','').replace('\t','').replace("// flash 오류를 우회하기 위한 함수 추가function _flash_removeCallback() {}"," ")


def crawling_post_date(url, header):

    req = requests.get(url, headers = header)
    req.encoding = None
    soup = BeautifulSoup(req.text, 'html.parser')
    
    # 기사 입력 날짜
    txt = soup.find('span', {'class' : 't11'})
    if not txt:
        txt = soup.find('div', {'class' : 'info'})

    if not txt:
        txt = soup.find('span', {'class' : 'author'})
    txt = txt.text
    return txt.replace('\n','').replace('\r','').replace('<br>','').replace('\t','')


def scrape(
    data,
    press_perm,
    n_press,
    query,
    sleep_sec,
    connection_reset_sleep,
    chrome_path,
    news_num,
    press_map_rev,
):
    news_dict = {}
    for i in range(len(data) - 1): # iterate over date range
        ds = data[i]
        de = data[i + 1]
        press_nm = press_perm[i][i % n_press]

        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")
        browser = webdriver.Chrome(chrome_path, options = options)
        # news_url = 'https://search.naver.com/search.naver?where=news&query={}&sm=tab_opt&sort=0&photo=0&field=0&pd=3&ds={}&de={}&docid=&related=0&mynews=1&office_type=1&office_section_code=1&news_office_checked={}&nso=so%3Ar%2Cp%3Afrom20160820to20210820&is_sug_officeid=0'.format(query, ds, de, press_nm)
        news_url = 'https://search.naver.com/search.naver?where=news&query={}&sm=tab_opt&sort=0&photo=0&field=0&pd=3&ds={}&de={}&docid=&related=0&mynews=1&office_type=1&office_section_code=1&news_office_checked={}&nso=so%3Ar%2Cp%3A&is_sug_officeid=0'.format(query, ds, de, press_nm)
        browser.get(news_url)
        time.sleep(sleep_sec)



        ################ 뉴스 크롤링 ########################

        print('\n\nStarting crawling for query "{}" in {} ({} ~ {}).'.format(query, press_map_rev[press_nm], ds, de))

        idx = 0
        # cur_page = 0.5

        pbar = tqdm(total=news_num ,leave = True)
        

        while idx < news_num:  # collect up to news_num limit

            # per page

            try:
                table = browser.find_element_by_xpath('//ul[@class="list_news"]')
            except selenium.common.exceptions.NoSuchElementException:
                print('Unable to find any results.')
                break

            if not table:
                print('Unable to find any results.')
                break
            li_list = table.find_elements_by_xpath('./li[contains(@id, "sp_nws")]')
            area_list = [li.find_element_by_xpath('.//div[@class="news_area"]') for li in li_list] 
            a_list = [area.find_element_by_xpath('.//div[@class="news_info"]') for area in area_list]
            b_list = [a.find_element_by_xpath('.//div[@class="info_group"]') for a in a_list] 
            c_list = [b.find_element_by_xpath('.//a[@class="info"]') for b in b_list]
            h_list = [element.get_attribute('href') for element in c_list]

            arts_thispage = len(li_list)
            naver_arts_thispage = len(c_list)



            # for n in c_list[:min(len(c_list), news_num - idx + 1)]:  # min(naver arts per this page, number left to do)
            # for n in c_list:  # min(naver arts per this page, number left to do)
            for n_url in h_list:  # min(naver arts per this page, number left to do)
                # try:
                #     n_url = n.get_attribute('href')
                # except Exception as e:
                #     print(n)
                #     print(e)
                headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'}
                try:
                    news_dict[i * news_num + idx] = {
                        'title' : crawling_title(n_url, headers), 
                        'url' : n_url,
                        'text' : crawling_main_text(n_url, headers),
                        'post_date' : crawling_post_date(n_url, headers),
                        'press': press_map_rev[press_nm],
                        'press_id' : press_nm,
                    }
                except requests.exceptions.ConnectionError:
                    time.sleep(connection_reset_sleep)
                    news_dict[i * news_num + idx] = {
                        'title' : crawling_title(n_url, headers), 
                        'url' : n_url,
                        'text' : crawling_main_text(n_url, headers),
                        'post_date' : crawling_post_date(n_url, headers),
                        'press': press_map_rev[press_nm],
                        'press_id' : press_nm,
                    }
                idx += 1
                pbar.update(1)
                if idx == news_num:
                    pbar.close()
                    break
            if idx < news_num:
                # cur_page +=1

                next_page_url = browser.find_element_by_xpath('//a[@class="btn_next"]').get_attribute('href')
                # next_page_url = [p for p in pages.find_elements_by_xpath('.//a') if p.text == str(cur_page)][0].get_attribute('href')

                if next_page_url is not None:
                    print('Continuing to the next page.')
                    browser.get(next_page_url)
                    time.sleep(sleep_sec)
                else:  # no more articles move to next category
                    print(' -> Unable to find additional results.')
                    idx = news_num
                    pbar.close()
                    break

    return news_dict


def main(
    date,
    sleep_sec,
    connection_reset_sleep,
    press_list,
    date_range,
    chrome_path,
    news_num,
    queries,
    save_path,
):
    ###### 언론사 코드 #######
    

    press_map = {'경향신문' : 1032, '조선일보' : 1023, '한겨레' : 1028, '연합뉴스' : 1001, 'JTBC' : 1437, 'KBS' : 1056, 'MBC' : 1214, 'SBS' : 1055, 'YTN' : 1052, '중앙일보' : 1025}

    # press_map = {'JTBC' : 1437, '연합뉴스' : 1001, 'MBC' : 1214,'KBS' : 1056 ,'SBS' : 1055,'YTN' : 1052}
    press_map_rev = {val: key for key, val in press_map.items()}
    press_dic = [press_map[press] for press in press_list]
    press_perm = list(itertools.permutations(press_dic))
    n_press = len(press_dic)

    ###### 날짜 ############
    data = pd.date_range(*date_range, freq = 'MS').tolist()
    for i, date in enumerate(data):
        data[i] = date.strftime("%Y.%m.%d")

    ####### 언론사별 본문 위치 태그 파싱 함수 ###########
    print('본문 크롤링에 필요한 함수를 로딩하고 있습니다...\n\n')# + '-' * 100)
        
    ############### 브라우저를 켜고 검색 키워드 입력 ####################    
    #press_nm = input('검색할 언론사 : ')


    # query = input('검색할 키워드  : ')

    for query_i, query in enumerate(queries):
        print('Query: {} ({}/{})'.format(query, query_i + 1, len(queries)))

        scraps = scrape(
            data,
            press_perm,
            n_press,
            query,
            sleep_sec,
            connection_reset_sleep,
            chrome_path,
            news_num,
            press_map_rev,
        )

        #### 데이터 전처리하기 ###################################################### 

        print('데이터프레임 변환\n')
        news_df = DataFrame(scraps).T

        csv_file_name = '{}_{}_{}.csv'.format(query, data[0], data[-1])
        csv_file = os.path.join(save_path, csv_file_name)

        # news_df.to_excel(xlsx_file)
        news_df.to_csv(csv_file, encoding='utf8')

        print('엑셀 저장 완료 | 경로 : {}\n'.format(csv_file))


if __name__ == '__main__':

    ###### parameters ##########
    sleep_sec = 1
    connection_reset_sleep = 1
    press_list = ['JTBC', '연합뉴스', 'MBC', 'KBS' ,'SBS', 'YTN']
    # queries = ['폭염', '코로나', '대설', '호우', '홍수', ]
    queries = [
        '가뭄', '가축 감염병', '강풍', '풍랑', '건조', '국가기간시설', '철도', '대설', '댐',
        '저수지', '제방', '미세먼지', '산불', '산사태', '수돗물', '안개', '인간 감염병', '전력',
        '지진', '지하철', '코로나19', '태풍', '통신장애', '폭염', '폭풍해일', '한파', '호우',
        '홍수', '화재', '폭발', '화학물질', '황사', '테러',
    ]

    # date_range = ('2015-01-01', '2021-08-01')
    date_range = ('2015-01-01', '2021-08-25')
    chrome_path = '/usr/bin/chromedriver'
    news_num = 100  # number of articles to collect from each key combination
    save_path = 'data/'

    ###### 날짜 저장 ##########
    date = str(datetime.now())
    date = date[:date.rfind(':')].replace(' ', '_')
    date = date.replace(':','시') + '분'
    
    ###### crawl ##########
    main(
        date,
        sleep_sec,
        connection_reset_sleep,
        press_list,
        date_range,
        chrome_path,
        news_num,
        queries,
        save_path,
    )
