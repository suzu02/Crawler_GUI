from collections import defaultdict
from datetime import timedelta
import logging
import queue
import random
import re
import threading
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
import pandas as pd
import requests
from requests.exceptions import ConnectionError, ReadTimeout


# GUIに表示させるためのログ設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
fmt = logging.Formatter('[%(asctime)s] (%(levelname)s) %(message)s')

CACHE_DIR = './.webcache'


class QueueHandler(logging.Handler):
    """
    ログの出力先をQueueに変更するための独自Handler
    loggingのHandlerクラスをを継承(emit関数をオーバーライド)
    """

    def __init__(self, log_queue):
        super().__init__()
        # インスタンス化時にQueueを受け取り、ログの出力先として定義
        self.log_queue = log_queue

    def emit(self, record):
        """ログ出力に応じて呼び出されるlogging.Handlerクラスの関数"""

        # ログ出力のタイミングで、ログをQueueにputすることで出力先を変更
        self.log_queue.put(record)


class Crawler(object):
    """
    crawlとscrape機能を持つcrawlerを定義

    attribute:
        self.crawler_alive_flag:
            crawler(スレッド)を終了させるためのbool値のフラグ

        self.crawler_event(threading.Eventオブジェクト):
            crawler(スレッド)の状態管理
            Eventのset()/wait()/clear()により、crawler(スレッド)の停止/再開を制御
            set()などのEvent操作はGUIのボタン操作により制御

        self.crawler_status:
            crawlerのより詳細な状態を、以下のstatusから設定することで管理
            GUIから状態変更は行わず、状態変化に連動したGUIの初期化等を行う

        self.status:
            crawlerのより詳細な状態を定義
                none: 初期状態、処理正常終了後
                run: 処理中
                pause: 停止中
                cancel: 取消終了後、エラーによる終了後
    """

    def __init__(self):
        self.start_url = (
            'https://books.toscrape.com/'
            'catalogue/category/books/fantasy_19/page-1.html'
        )
        self.encoding = 'utf-8'
        # sessionは、HTTPヘッダー等の設定やユーザー認証情報を引き継ぐほか、
        # 確立したTCPコネクションも引き継ぐのでパフォーマンス向上
        session = requests.Session()
        self.session_cache = CacheControl(session, FileCache(CACHE_DIR))
        # GUIのボタン操作によりappモジュールからファイルパスが渡される
        self.output_path = None
        self.crawler_event = threading.Event()
        self.status = ('none', 'run', 'pause', 'cancel')
        self.crawler_status = self.status[0]

        # QueueHandlerによるログの出力先としてQueueをインスタンス化
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        self.queue_handler.setFormatter(fmt)
        logger.addHandler(self.queue_handler)

    def start_crawler_thread(self):
        """crawlerのスレッド作成/開始処理"""

        self.execute_time = time.time()
        self.crawler_thread = threading.Thread(target=self.run_crawler)

        # crawlerの状態変更等
        self.crawler_status = self.status[1]
        self.crawler_alive_flag = True

        self.crawler_thread.start()

        # ログに表示するカウント関連の初期化
        self.result_counter = {
            'Request sent count': 0,
            'Response received count': 0,
            'Status code count': defaultdict(int),
            'Scraped content count': 0,
        }

    def run_crawler(self):
        """作成したスレッド上で処理されるcrawlerの全体処理"""

        logger.info('----- Crawler Start -----')

        # crawlerの状態変更等
        self.crawler_event.set()
        self.crawler_status = self.status[1]

        # 最終的なscrapeデータの格納場所
        self.data_list = []
        # ログ表示用のページ数
        self.current_page = 1

        time.sleep(random.randint(1, 3))
        # 自己定義した関数内でリクエスト
        r = self.try_request(self.start_url)
        r.encoding = self.encoding

        # start_urlのレスポンスを元に詳細ページのcrawl/scrape実行
        self.scraping_detail_page(r)

        # 正常終了した場合だけjsonファイル出力
        if not self.crawler_status == self.status[3]:
            self.output_file()
            # crawlerの状態等変更
            self.crawler_status = self.status[0]

    def try_request(self, url):
        """リクエスト処理を一元管理"""

        # リクエストとレスポンスの総数を加算
        self.result_counter['Request sent count'] += 1
        self.result_counter['Response received count'] += 1

        try:
            r = self.session_cache.get(url, timeout=3.5)
        # ネットワークの未接続等
        except (ConnectionError, ReadTimeout):
            logger.error('[Request] ConnectionError or ReadTimeoutError')
            logger.info('===== Crawler Finished =====')

            # crawlerの状態等変更
            self.crawler_status = self.status[3]

            # 処理終了に際して結果をログ表示
            self.display_processing_result()

            # raiseでcrawlerのスレッド終了
            # GUIでは上記のstatus[3]を検知して表示内容等の初期化
            raise Exception('[Request] ConnectionError or ReadTimeoutError')
        else:
            logger.info(f'Request url: {r.url}')
            logger.info(f'From cache: {r.from_cache}')
            logger.info(f'Status code: {r.status_code}')

            # ログ表示用のカウント
            # 既存のコードを検知した場合はvalueだけ加算、
            # 新たなコードを検知した場合はkeyとvalueを新たに定義して追加
            self.result_counter['Status code count'][r.status_code] += 1

            return r

    def scraping_detail_page(self, r):
        """
        詳細ページのcrawl/scrape処理を管理

        Note(処理の流れ):
            1. start_url(1ページ分)から各詳細ページのURL取得
            2. start_urlに次ページがある場合はそのURL取得
            3. 上記1で取得した各詳細ページのURLを順にcrawl/コンテンツのscrape処理
            4. 上記2で次ページがある場合は、上記1に戻り、次ページに対して同様に処理

            上記1~4の処理を次ページがある限り繰り返す
        """

        # start_url(詳細ページをまとめたページ)のレスポンスから各詳細ページのurlをscrape
        detail_urls = self.scrape_detail_page_urls(r)

        # start_urlのページに、次ページのURLがある場合はそのURLをscrape
        next_page_url = self.search_next_page(r)

        # 各詳細ページのurlを順番にcrawl/scrape
        # thread.Eventやフラグにおいて制御するのは以下のループ処理
        for i, url in enumerate(detail_urls, start=1):
            # ループ途中でフラグFalseを検知した場合はスレッド終了
            # フラグはGUIにより特定のボタン操作を行うことで操作
            if not self.crawler_alive_flag:
                logger.info('===== Crawler Finished =====')

                # crawlerの状態等変更
                self.crawler_status = self.status[3]

                # 処理終了に際して結果をログ表示
                self.display_processing_result()

                # エラー終了ではないためreturn Noneでこの処理を終了
                # その後、呼び出し元の処理に戻り、上記のstatus[3]によりファイル出力はせずスレッドも終了
                return None

            logger.info(
                f'----- Request detail page({self.current_page}-{i}) -----')

            time.sleep(random.randint(1, 3))
            # 自己定義した関数内でリクエスト
            r = self.try_request(url)
            r.encoding = self.encoding

            # 詳細ページから各コンテンツのscrape
            data = self.scrape_detail_page_content(r)
            self.data_list.append(data)

            # thread.Eventによるスレッドの停止/再開処理
            # thread.Eventの状態Falseを検知した場合、event.wait()実行によりスレッド停止
            # 上記の状態でevent.set()が実行されると、状態はTrueに変更されスレッドも再開
            # thread.Eventの状態は、GUIの特定のボタン操作により変更、
            # スレッド処理のループ上に以下の記述することで、任意のタイミングで制御可能
            if not self.crawler_event.is_set():
                logger.info('----- Crawler Pause -----')
                # 処理停止にあたりcrawlerの状態等変更(必ずwait()より前に記述)
                self.crawler_status = self.status[2]
                self.crawler_event.wait()
                # 処理開始にあたりcrawlerの状態等変更
                self.crawler_status = self.status[1]

        logger.info(f'----- Scrape completed page[{self.current_page}] -----')

        # 次ページのurlがある場合の処理
        if next_page_url:
            logger.info('----- Request next page -----')
            logger.info(f'next page url: {next_page_url}')

            # ログ表示用のページ数を加算
            self.current_page += 1

            time.sleep(random.randint(1, 3))
            # 自己定義した関数内で次ページのURLにリクエスト
            r = self.try_request(next_page_url)
            r.encoding = self.encoding

            # 自分自身を呼び出すことで、次ページのURLがある限りループ
            self.scraping_detail_page(r)
        # 次ページのurlがない場合は処理終了、これに伴いスレッドも終了
        else:
            logger.info('===== Crawler Finished =====')
            self.display_processing_result()

    def scrape_detail_page_urls(self, r):
        """start_urlのレスポンスから各詳細ページのURLをscrape"""

        logger.info('Scrape detail page urls')

        soup = BeautifulSoup(r.text, 'lxml')
        # 詳細ページのURLにあたる個所をcssセレクターですべて抽出
        urls = soup.select('h3 > a')

        for url in urls:
            abs_url = self.convert_absolute_url(url.attrs['href'])
            yield abs_url

    def convert_absolute_url(self, url):
        """相対URLから絶対URLに変換"""

        # 余分な文字を削除
        molding_url = url.replace('../', '')

        # ページURLの場合
        if re.search(r'html$', molding_url):
            return urljoin(
                'https://books.toscrape.com/catalogue/', molding_url)
        # 画像URLの場合
        else:
            return urljoin('https://books.toscrape.com/', molding_url)

    def search_next_page(self, r):
        """次ページURLの有無に応じた処理"""

        soup = BeautifulSoup(r.text, 'lxml')

        try:
            url = soup.select_one('li.next > a').attrs['href']
        # 次ページのURLがない場合(抽出できない場合)
        except AttributeError:
            return None
        # 次ページのURLがある場合
        else:
            next_page_url = urljoin(
                'https://books.toscrape.com/'
                'catalogue/category/books/fantasy_19/',
                url,
            )
            return next_page_url

    def scrape_detail_page_content(self, r):
        """詳細ページから各コンテンツをscrape"""

        logger.info('Scrape detail page content')

        soup = BeautifulSoup(r.text, 'lxml')

        # 初めに取得したいデータに応じて大きく抽出
        contents = soup.select_one('article > div.row')
        table = soup.find('table')

        # 画像は絶対URLに変換する必要があるので先に抽出
        image_rel_url = contents.select_one('div.item > img').attrs['src']
        image_abs_url = self.convert_absolute_url(image_rel_url)

        data = {
            'url': r.url,
            'title': contents.find('h1').text,
            # bs4独自の記述として、要素に特定の文字が含まれているか-soup-contains()で抽出
            'price': table.select_one('th:-soup-contains("excl")+td').text,
            # .attrsで抽出した要素に複数の属性が存在する場合リストで抽出
            'star': self.convert_text_to_number(contents.select_one(
                'div.product_main p.star-rating').attrs['class'][1]),
            'reviews': int(
                table.select_one('th:-soup-contains("reviews")+td').text),
            'stock': self.extract_stock(table.select_one(
                'th:-soup-contains("Availability")+td').text),
            'upc': table.select_one('th:-soup-contains("UPC")+td').text,
            'image_url': image_abs_url,
        }

        [logger.info(f'- {k}: {v}') for k, v in data.items()]

        # ログ表示用のscrapeコンテンツ数の加算
        self.result_counter['Scraped content count'] += len(data)

        return data

    def extract_stock(self, element):
        """scrapeデータの整形(stock数の抽出)"""

        if element:
            m = re.search('In stock', element)
            if m:
                return int(
                    element.replace(
                        'In stock (', '').replace(' available)', ''))
            else:
                return 0
        return 0

    def convert_text_to_number(self, element):
        """scrape後のデータ整形(テキストから数字へ変換)"""

        convert_pattern = {
            'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5
        }
        if element:
            try:
                return convert_pattern[element]
            except KeyError:
                return 0
        return 0

    def display_processing_result(self):
        """処理終了のタイミングで、結果をログ出力"""

        for k, v in self.result_counter.items():
            # ステータスコードのvalueはdictのため、items()のループでさらに取り出す
            if k == 'Status code count':
                for status_code, count in v.items():
                    logger.info(f'* {k}: {status_code}[{count}]')
                continue
            logger.info(f'* {k}: {v}')

        elapsed_time = int(time.time() - self.execute_time)
        logger.info(f'* Elapsed time: {timedelta(seconds=elapsed_time)}')

    def output_file(self):
        """scrapeデータのjsonファイル出力処理"""

        df = pd.DataFrame(self.data_list)
        # orientは、どういった形式で出力するか、
        # force_asciiは、全角文字などの非ascii文字をunicodeエスケープ(\u3042等)するかどうか
        df.to_json(self.output_path, orient='records', force_ascii=False)

        logger.info(f'* Output the file {self.output_path}')
