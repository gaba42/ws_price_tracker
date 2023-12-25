import requests
from glob import glob
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from time import sleep

# http://www.networkinghowtos.com/howto/common-user-agent-list/
HEADERS = ({'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5'})


def search_product_list(interval_count = 1, interval_hours = 6):
    """
    이 함수는 헤더와 함께 TRACKER_PRODUCTS.csv라는 이름의 csv 파일을 로드합니다: [url, code, buy_below] 헤더를 사용합니다.
    이 함수는 ./trackers에서 파일을 찾습니다.
    
    또한 결과 저장을 시작하려면 ./search_history 폴더 아래에 SEARCH_HISTORY.xslx라는 파일이 필요합니다.
    스크립트를 처음 사용할 때는 빈 파일을 사용할 수 있습니다.
    
    그러면 이전 결과와 새 결과가 모두 SEARCH_HISTORY_{datetime}.xlsx라는 새 파일에 저장됩니다.
    이 파일은 스크립트가 다음에 실행될 때 기록을 가져오는 데 사용할 파일입니다.

    매개변수
    ----------
    interval_count : TYPE, 선택 사항
        . 기본값은 1입니다. 스크립트에서 전체 목록에서 검색을 실행할 반복 횟수입니다.
    interval_hours : TYPE, 선택 사항
        . 기본값은 6입니다.

    반환값
    -------
    이전 검색 기록과 현재 검색 결과가 포함된 새 .xlsx 파일

    """
    prod_tracker = pd.read_csv('trackers/TRACKER_PRODUCTS.csv', sep=',')
    prod_tracker_URLS = prod_tracker.url
    tracker_log = pd.DataFrame()
    now = datetime.now().strftime('%Y-%m-%d %Hh%Mm')
    interval = 0 # counter reset
    
    while interval < interval_count:

        for x, url in enumerate(prod_tracker_URLS):
            page = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(page.content, features="lxml")
            
            #제품 title
            title = soup.find(id='productTitle').get_text().strip()
            
            # 제품 가격이 없을 때 스크립트가 충돌하는 것을 방지
            try:
                # price = float(soup.find(id='priceblock_ourprice').get_text().replace('.', '').replace('€', '').replace(',', '.').strip())
                price = float(soup.find('span', 'a-offscreen').get_text().replace('.', '').replace('¥', '').replace(',', ''))
            except:
                # amazon.com $$ 가격
                try:
                    price = float(soup.find(id='priceblock_saleprice').get_text().replace('$', '').replace(',', '').strip())
                except:
                    price = ''

            try:
                # review_score = float(soup.select('i[class*="a-icon a-icon-star a-star-"]')[0].get_text().split(' ')[0].replace(",", "."))
                review_score = float(soup.select('#acrPopover .a-color-base')[0].get_text().strip())
                # review_count = int(soup.select('#acrCustomerReviewText')[0].get_text().split(' ')[0].replace(".", ""))
                review_count = int(soup.select('#acrCustomerReviewText')[0].get_text().split(' ')[0].replace(',', ''))
            except:
                # 리뷰 점수가 다른데에 있기도 해서 추가한 statement
                try:
                    review_score = float(soup.select('i[class*="a-icon a-icon-star a-star-"]')[1].get_text().split(' ')[0].replace(",", "."))
                    review_count = int(soup.select('#acrCustomerReviewText')[0].get_text().split(' ')[0].replace(".", ""))
                except:
                    review_score = ''
                    review_count = ''
            
            
            # 재고 확인 
            try:
                available = soup.select("#availability > span.a-size-base.a-color-price.a-text-bold")[
                    0].get_text().strip()
                current_stat = 'Out'
                if stock in current_stat:
                    stock = 'Out of Stock'
            except:
                stock = 'Available'

            log = pd.DataFrame({'date': now.replace('h',':').replace('m',''),
                                'code': prod_tracker.code[x], # TRACKER_PRODUCTS 파일에서 가져옴
                                'url': url,
                                'title': title,
                                'buy_below': prod_tracker.buy_below[x], # 가격도 마찬가지로 TRACKER_PRODUCTS 파일에서 가져온다
                                'price': price,
                                'stock': stock,
                                'review_score': review_score,
                                'review_count': review_count}, index=[x])

            try:
                # 이메일 알람 코드 추가할 부분
                if price < prod_tracker.buy_below[x]:
                    print('************************ 구매 가능한 상태! '+prod_tracker.code[x]+' ************************')
            
            except:
                # price를 못 가져올 때 에러가 남
                pass

            # tracker_log = tracker_log.append(log)
            tracker_log = pd.concat([tracker_log, log])
            print('appended '+ prod_tracker.code[x] +'\n' + title + '\n\n')
            sleep(5)
        
        interval += 1# counter update
        
        sleep(interval_hours*1*1)
        print('end of interval '+ str(interval))
    
    # 실행 뒤 마지막 서치 기록 확인 후 새로운 서치 결과를 추가해서 새로운 파일 생성 
    last_search = glob('./search_history/*.xlsx')[-1] # 파일 경로
    search_hist = pd.read_excel(last_search)
    final_df = pd.concat([search_hist, tracker_log], sort=False)

    final_df.to_excel('search_history/SEARCH_HISTORY_{}.xlsx'.format(now), index=False)
    print('end of search')

search_product_list()
