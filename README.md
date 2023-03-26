# Crawler_GUI
趣味で作成したWebスクレイピング用のGUIアプリケーションです。

![python](https://img.shields.io/badge/python-v3.11-blue)
![beautifulsoup4](https://img.shields.io/badge/beautifulsoup4-v4.12.0-blue)
![CacheControl](https://img.shields.io/badge/CacheControl-v0.12.11-blue)
![lxml](https://img.shields.io/badge/lxml-v4.9.2-blue)
![pandas](https://img.shields.io/badge/pandas-v1.5.3-blue)
![requests](https://img.shields.io/badge/requests-v2.28.2-blue)
![license](https://img.shields.io/badge/license-MIT-green)


## 概要
* 特定のWebサイトを対象として、CrawlerによるWebスクレイピングを行います。
* Crawlerは、主にrequestsとBeautifusoup4を組み合わせて作成しています。
* リクエストごとに1~3秒の待機時間を設けています。
* アプリのボタン操作により、Crawlerの処理開始/停止/取消などを制御することができます。
* アプリの「ログウィンドウ」には、処理の進捗状況(Crawlerのログ)が表示されます。
* Crawlerの処理が正常終了した場合、スクレイピングデータがjsonファイルとして、任意のディレクトリに保存されます。
* 対象のWebサイトは、スクレイピング練習用サイト「[https://books.toscrape.com](https://books.toscrape.com)」を利用させていただいております。
* 利用にあたっては、ネットワーク接続が必要です。


  
## 必要な環境
アプリケーションを利用するためには、以下の環境が必要です。(動作確認はWindowsのみ)
* [Python](https://www.python.org/) [3.11]
* [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/bs4/) [4.12.0] `MIT License`
* [CacheControl](https://github.com/ionrock/cachecontrol) [0.12.11] `Apache Software License`
* [lxml](https://lxml.de/) [4.9.2] `BSD License`
* [pandas](https://pandas.pydata.org) [1.5.3] `BSD License`
* [requests](https://requests.readthedocs.io) [2.28.2] `Apache Software License`

このリポジトリをクローンして、`pip install -r requirements.txt`コマンドを実行することで、任意の環境に必要なライブラリがまとめてインストールされます。  

また、以下の手順により、実行ファイル化(exe化)して使用することも可能です。



## exe化の手順([pyinstaller](https://pyinstaller.org/en/stable/))
1. クローンしたディレクトリまで移動
2. 次のコマンドを実行  
`pyinstaller --hidden-import beautifulsoup4 --hidden-import CacheControl[filecache] --hidden-import pandas --hidden-import requests --noconsole app.py`
3. 「dist」ディレクトリが作成されるので、配下の「app」ディレクトリに`app.exe`ファイルがあることを確認
4. クローンしたディレクトリ配下の「icon.ico」ファイルと「.webcache」ディレクトリを、上記3の「dist」ディレクトリ配下にコピー&ペースト

上記の手順は新たな仮想環境を作成して、必要なライブラリをインストールしてから実行することを推奨します。



## 使用方法
アプリを起動すると以下のような画面が表示されます。

<image width='700' alt='初期画面' src=https://user-images.githubusercontent.com/117723810/227696428-895e0bf7-5c55-4339-b571-673976b781d5.png>



### 1. jsonファイルの出力先を設定
出力されるjsonファイルの保存場所を設定してください。

アプリの「選択」ボタンをクリックすると、以下の画面が表示されます。  

<image width='700' alt='ファイルダイアログ' src=https://user-images.githubusercontent.com/117723810/227696422-a27715f0-840e-489b-8530-0d66ed3bf150.png>

デフォルトのディレクトリは「ダウンロード」、ファイル名は「(起動時のタイムスタンプ)_scrape.json」としています。  
変更される場合は、ディレクトリやファイル名を変更後、「保存」ボタンをクリックしてください。  
ファイル名を変更する場合、適切ではない記号等が含まれていると、エラーメッセージが表示されデフォルトに戻ります。

なお、ファイル名の末尾は、拡張子「.json」を付けなくても自動で付与されます。  


### 2. 開始ボタンをクリック
開始ボタンをクリックするとWebスクレイピングが開始され、「ログウィンドウ」に処理状況が表示されます。  

<image width='700' alt='開始後の画面' src=https://user-images.githubusercontent.com/117723810/227696413-e4db9a60-e212-490c-95af-5b37694068c9.png>
<image width='700' alt='処理中の画面' src=https://user-images.githubusercontent.com/117723810/227696424-f29ccc15-eb84-4543-a9c6-932bdf20278f.png>

必要な手順は以上です。  

スクレイピングが正常に終了すると、上記1で設定した場所にjsonファイルが保存されます。  

<image width='700' alt='終了後の画面' src=https://user-images.githubusercontent.com/117723810/227703203-8d8004da-58ac-42ce-967a-95d94f532ee3.png>


### その他の操作

#### 処理の停止/再開
アプリの「停止」ボタンをクリックすると処理が停止、ボタンのテキストが「再開」に切り替わります。   
上記の状態で「再開」ボタンをクリックすると処理が再開、ボタンのテキストが「停止」に切り替わります。  

<image width='700' alt='停止中の画面' src=https://user-images.githubusercontent.com/117723810/227696418-17ad1653-5bd2-495c-8625-ff0ab14fec08.png>


#### 処理の取消
アプリの「取消」ボタンをクリックしてください。  
以下の確認画面が表示されるので、「OK」ボタンをクリックすると処理は取り消されます。  

<image width='400' alt='処理取消の確認画面' src=https://user-images.githubusercontent.com/117723810/227696527-a9803939-e0da-447e-a2b0-9ef11fbfbde4.png>

処理の途中で取り消した場合は、jsonファイルは出力されません。  
取り消し後、再び「開始」ボタンをクリックすると新たに処理が開始されます。  


#### アプリの終了
アプリの「終了」ボタン、もしくは「✕」ボタンをクリックしてください。  
処理の途中でクリックした場合、以下の確認画面が表示されるので、「OK」ボタンをクリックすると処理を終了してアプリを閉じます。  

<image width='400' alt='アプリ終了の確認画面' src=https://user-images.githubusercontent.com/117723810/227696339-adc8e0bc-60b5-4e14-b876-dec84088effd.png>

処理の途中で終了した場合は、jsonファイルは出力されません。  

  

## お問い合わせ
質問などありましたら気軽にご連絡ください。  
mail: suzucd02@gmail.com  
twitter:@suzu20439071  
Github: suzu02  



## License
LC Manager is licensed under the MIT license.  
Copyright &copy; 2023, suzu02  
