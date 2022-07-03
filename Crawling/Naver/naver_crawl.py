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
import pickle, progressbar, json, glob, time
from tqdm import tqdm
import itertools

###### 날짜 저장 ##########
date = str(datetime.now())
date = date[:date.rfind(':')].replace(' ', '_')
date = date.replace(':','시') + '분'

sleep_sec = 0.5

###### 언론사 코드 #######
news_dict = {}

# press_list = {'경향신문' : 1032, '조선일보' : 1023, '한겨레' : 1028, '연합뉴스' : 1001, 'JTBC' : 1437, 'KBS' : 1056, 'MBC' : 1214, 'SBS' : 1055, 'YTN' : 1052, '중앙일보' : 1025}

press_list = {'연합뉴스' : 1001, 'MBC' : 1214,'KBS' : 1056 ,'SBS' : 1055,'YTN' : 1052}
press_dic = list(press_list.values())
press_perm = list(itertools.permutations(press_dic))
###### 날짜 ############
data = pd.date_range('2015-01-01', '2021-08-01', freq = 'MS').tolist()
for i, date in enumerate(data):
    data[i] = date.strftime("%Y.%m.%d")

####### 언론사별 본문 위치 태그 파싱 함수 ###########
print('본문 크롤링에 필요한 함수를 로딩하고 있습니다...\n' + '-' * 100)

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
        txt = soup.find('div', {'id' : 'article_body font1 size3'})
    txt = txt.text
        
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
    
############### 브라우저를 켜고 검색 키워드 입력 ####################    
#press_nm = input('검색할 언론사 : ')


query = input('검색할 키워드  : ')

for i in range(len(data) - 1):
     ds = data[i]
     de = data[i + 1]
     news_num = 10
     press_nm = press_perm[i][i % len(press_dic)]
#ds = input('검색 시작 날짜 : 1990.01.01 과 같이 입력 : ')
#de = input('검색 마지막 날짜 : 2021.08.20과 같이 입력 : ')
#news_num = int(input('수집 뉴스의 수(숫자만 입력) : '))

     print('\n' + '=' * 100 + '\n')

     print('브라우저를 실행시킵니다(자동 제어)\n')
     chrome_path = 'C:/chromedriver/chromedriver.exe'
     options = webdriver.ChromeOptions()
     options.add_experimental_option("excludeSwitches", ["enable-logging"])
     browser = webdriver.Chrome(chrome_path, options = options)
     news_url = 'https://search.naver.com/search.naver?where=news&query={}&sm=tab_opt&sort=0&photo=0&field=0&pd=3&ds={}&de={}&docid=&related=0&mynews=1&office_type=1&office_section_code=1&news_office_checked={}&nso=so%3Ar%2Cp%3Afrom20160820to20210820&is_sug_officeid=0'.format(query, ds, de, press_nm)
     browser.get(news_url)
     time.sleep(sleep_sec)


######### 언론사 선택 및 confirm #####################
# print('설정한 언론사를 선택합니다.\n')

# search_opn_btn = browser.find_element_by_xpath('.//a[@class="btn_option _search_option_open_btn"]')
# search_opn_btn.click()
# time.sleep(sleep_sec)

# bx_press = browser.find_element_by_xpath('//div[@role="listbox" and @class="api_group_option_sort _search_option_detail_wrap"]//li[@class="bx press"]')
# # 기준 두번 째(언론사 분류순) 클릭하고 오픈하기
# press_tablist = bx_press.find_elements_by_xpath('.//div[@role="tablist" and @class="option"]/a')
# press_tablist[1].click()
# time.sleep(sleep_sec)

# # 첫 번째 것(언론사 분류선택)
# bx_group = bx_press.find_elements_by_xpath('.//div[@class="api_select_option type_group _category_select_layer"]/div[@class="select_wrap _root"]')[0]

# press_kind_bx = bx_group.find_elements_by_xpath('.//div[@class="group_select _list_root"]')[0]
# press_kind_btn_list = press_kind_bx.find_elements_by_xpath('.//ul[@role="tablist" and @class="lst_item _ul"]/li/a')


# for press_kind_btn in press_kind_btn_list:
    
#     # 언론사 종류를 순차적으로 클릭(좌측)
#     press_kind_btn.click()
#     time.sleep(sleep_sec)
    
#     # 언론사선택(우측)
#     press_slct_bx = bx_group.find_elements_by_xpath('.//div[@class="group_select _list_root"]')[1]
#     # 언론사 선택할 수 있는 클릭 버튼
#     press_slct_btn_list = press_slct_bx.find_elements_by_xpath('.//ul[@role="tablist" and @class="lst_item _ul"]/li/a')
#     # 언론사 이름들 추출
#     press_slct_btn_list_nm = [psl.text for psl in press_slct_btn_list]
    
#     # 언론사 이름 : 언론사 클릭 버튼 인 딕셔너리 생성
#     press_slct_btn_dict = dict(zip(press_slct_btn_list_nm, press_slct_btn_list))
    
#     # 원하는 언론사가 해당 이름 안에 있는 경우
#     # 1) 클릭하고
#     # 2) 더이상 언론사분류선택 탐색 중지
#     if press_nm in press_slct_btn_dict.keys():
#         print('<{}> 카테고리에서 <{}>를 찾았으므로 탐색을 종료합니다'.format(press_kind_btn.text, press_nm))
        
#         press_slct_btn_dict[press_nm].click()
#         time.sleep(sleep_sec)
        
#         break


################ 뉴스 크롤링 ########################

     print('\n크롤링을 시작합니다.')
# ####동적 제어로 페이지 넘어가며 크롤링
     idx = 0
     cur_page = 1

     pbar = tqdm(total=news_num ,leave = True)
        
     while idx < news_num:
        
        table = browser.find_element_by_xpath('//ul[@class="list_news"]')
        if not table:
            break
        li_list = table.find_elements_by_xpath('./li[contains(@id, "sp_nws")]')
        area_list = [li.find_element_by_xpath('.//div[@class="news_area"]') for li in li_list] 
        a_list = [area.find_element_by_xpath('.//div[@class="news_info"]') for area in area_list]
        b_list = [a.find_element_by_xpath('.//div[@class="info_group"]') for a in a_list] 
        c_list = [b.find_element_by_xpath('.//a[@class="info"]') for b in b_list]


        for n in c_list[:min(len(c_list), news_num-idx+1)]:
            n_url = n.get_attribute('href')
            headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'}

            news_dict[i * news_num + idx] = {'title' : crawling_title(n_url, headers), 
                            'url' : n_url,
                            'text' : crawling_main_text(n_url, headers),
                            'post_date' : crawling_post_date(n_url, headers),
                            'press' : press_nm}
            
            idx += 1
            pbar.update(1)
            
            if idx < news_num:
        #     cur_page +=1

        #     pages = browser.find_element_by_xpath('//div[@class="sc_page_inner"]')
        #     next_page_url = [p for p in pages.find_elements_by_xpath('.//a') if p.text == str(cur_page)][0].get_attribute('href')

        #     browser.get(next_page_url)
                time.sleep(sleep_sec)
            else:
                pbar.close()
            
            #print('\n브라우저를 종료합니다.\n' + '=' * 100)
            #time.sleep(2)
            #browser.close()
                break

#### 데이터 전처리하기 ###################################################### 

print('데이터프레임 변환\n')
news_df = DataFrame(news_dict).T

folder_path = os.getcwd()+'\\news_data'
xlsx_file_name = '{}_{}_{}.xlsx'.format(query, ds, de)

news_df.to_excel(xlsx_file_name)

print('엑셀 저장 완료 | 경로 : {}\\{}\n'.format(folder_path, xlsx_file_name))

os.startfile(folder_path)

    # print('=' * 100 + '\n결과물의 일부')
news_df
