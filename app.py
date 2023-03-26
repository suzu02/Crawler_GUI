from collections import defaultdict
from datetime import datetime
import os
import queue
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from crawler import Crawler


class ControlUi(object):
    """Crawlerコントロール部分における各widget/機能の定義"""

    def __init__(self, frame, crawler, master, log_window):
        # Appクラスで定義したCrawlerコントロール用のラベルフレーム
        self.frame = frame
        # Appクラスでインスタンス化されたcrawlerモジュールを属性として定義
        self.crawler = crawler
        # Appクラスで定義されたGUI本体(終了ボタンや✕ボタン押下時の処理用)
        self.master = master
        # LogWindowUiクラスで定義されたwidget(ログクリアボタン押下時の処理用)
        self.scrolled_text = log_window.scrolled_text

        self.create_output_path()
        self.create_widget()

    def create_output_path(self):
        """jsonファイル出力時のデフォルトパス作成"""

        self.date_time = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')
        # environ['USERPROFILE']は、Windowsにおける「C:\Users\(ユーザー名)」
        # よって以下は、ユーザーのダウンロードディレクトリを指す
        self.default_output_dir = os.path.join(
            os.environ['USERPROFILE'], 'Downloads')
        self.default_output_file = self.date_time + '_scrape.json'
        self.default_output_path = os.path.join(
            self.default_output_dir, self.default_output_file
            ).replace(os.sep, '/')

    def create_widget(self):
        """Crawlerコントロール部分の各widget定義"""

        frame = tk.Frame(self.frame)
        frame.grid(column=0, row=0, sticky='nesw', padx=15, pady=10)

        # 「対象のURL」のラベル
        tk.Label(
            frame,
            text='対象のURL ( Crawlerの開始URL )',
        ).grid(column=0, row=0, sticky='w')

        # widgetのstate=readonlyに伴うテキスト表示等のため
        target_url_var = tk.StringVar()
        target_url_var.set(self.crawler.start_url)

        # 「対象のURL」のエントリー
        target_url = tk.Entry(
            frame,
            width=60,
            textvariable=target_url_var,
            state='readonly',
        )
        target_url.grid(column=0, row=1, ipady=2, sticky='w')

        # 「対象のURL」のスクロールバー
        target_url_xbar = tk.Scrollbar(
            frame, orient=tk.HORIZONTAL, command=target_url.xview)
        target_url['xscrollcommand'] = target_url_xbar.set
        target_url_xbar.grid(column=0, row=2, sticky='ew')

        # 「ファイルの出力先」のラベル
        tk.Label(
            frame,
            text='ファイルの出力先',
        ).grid(column=0, row=3, sticky='w')

        # widgetのstate=readonlyに伴うテキスト表示等のため
        self.output_path_var = tk.StringVar()
        self.output_path_var.set(self.default_output_path)

        # 「ファイルの出力先」のエントリー
        output_path = tk.Entry(
            frame,
            width=60,
            textvariable=self.output_path_var,
            state='readonly',
        )
        output_path.grid(column=0, row=4, ipady=2, sticky='w')

        # ファイルダイアログ表示の「選択」ボタン
        self.file_dialog_btn = tk.Button(
            frame,
            width=7,
            text='選択',
            command=self.display_file_dialog,
        )
        self.file_dialog_btn.grid(column=1, row=4)

        # 「ファイルの出力先」のスクロールバー
        output_path_xbar = tk.Scrollbar(
            frame, orient=tk.HORIZONTAL, command=output_path.xview)
        output_path['xscrollcommand'] = output_path_xbar.set
        output_path_xbar.grid(column=0, row=5, sticky='ew')

        # メッセージ部分のラベルフレーム
        message_frame = tk.LabelFrame(
            frame,
            text='メッセージ',
            width=60,
            height=50,
            borderwidth=1,
        )
        message_frame.grid(
            column=0,
            row=6,
            columnspan=2,
            pady=(10, 0),
            sticky='ew',
        )

        # メッセージ部分のテキスト情報のラベル
        self.message_var = tk.StringVar()
        self.message_var.set('Crawler待機中')
        self.message = tk.Label(
            message_frame,
            textvariable=self.message_var,
            fg='black',
        )
        self.message.grid(column=0, row=0, sticky='w')

        # 各操作ボタン配置のためのフレーム
        btn_frame = tk.Frame(frame)
        btn_frame.grid(column=0, row=7, pady=(20, 0), sticky='w')

        # 開始ボタン
        self.start_btn = tk.Button(
            btn_frame,
            text='開始',
            command=self.start,
            width=7,
        )
        self.start_btn.grid(column=0, row=0)

        # 停止ボタン
        self.pause_btn = tk.Button(
            btn_frame,
            text='停止',
            command=self.pause,
            width=7,
            state='disabled',
        )
        self.pause_btn.grid(column=1, row=0, padx=10)

        # 取消ボタン
        self.cancel_btn = tk.Button(
            btn_frame,
            text='取消',
            command=self.cancel,
            width=7,
            state='disabled',
        )
        self.cancel_btn.grid(column=2, row=0)

        # ログクリアボタン
        self.clear_btn = tk.Button(
            btn_frame,
            text='ﾛｸﾞｸﾘｱ',
            command=self.clear_log,
            width=7,
        )
        self.clear_btn.grid(column=4, row=0, padx=(30, 0))

        # 終了ボタン
        tk.Button(
            btn_frame,
            text='終了',
            command=self.quit,
            width=7,
        ).grid(column=5, row=0, padx=(10, 0))

    def display_file_dialog(self):
        """
        ファイルダイアログの表示と入力値の受け渡し処理

        Note
            使用したファイルダイアログでは、filetypeに拡張子の強制力はなく、
            また、ファイル名に適切ではない記号等が含まれていても許容されるため、
            入力値の検証処理は別途定義
        """

        # 保存ボタン押下時はそのファイルパス、cancel/✕ボタン押下時はNoneが返る
        user_entry_value = filedialog.asksaveasfilename(
            title='ファイルの名前 / 出力先の設定',
            filetypes=[("json", ".json"), ],
            # ダイアログの初期表示ディレクトリ
            initialdir=self.default_output_dir,
            # ダイアログの初期表示ファイル名
            initialfile=self.default_output_file,
            # 拡張子の記述を省略した際に自動で付される拡張子
            defaultextension='json',
        )

        if user_entry_value:
            # ファイルパスの検証結果に応じた処理
            if self.validate_path(user_entry_value):
                # ダイアログの設定値をエントリーに反映
                self.output_path_var.set(user_entry_value)
                # デフォルトのファイル名を上書きすることで、
                # 再度ダイアログを開いた際、ダイアログのファイル名には上書きしたファイル名が表示される
                self.default_output_file = os.path.basename(
                    self.output_path_var.get())

                self.message_var.set('Crawler待機中')
                self.message.config(fg='black')
            # 検証結果に問題がある場合
            else:
                # 念のためデフォルトのファイルパスを再セット
                self.output_path_var.set(self.default_output_path)

                self.message.config(fg='red')
                self.message_var.set(
                    '入力されたファイル名は、'
                    '拡張子の誤り or 適切ではない記号が含まれています。'
                )

    def validate_path(self, user_entry_value):
        """ファイルダイアログにおける入力値の検証処理"""

        # 検証に必要なファイル名を取得
        file_name = os.path.basename(user_entry_value)

        # 拡張子と記号(-ハイフンと_アンダースコアのみ)の検証
        m = re.match(r'[\w-]+\.json$', file_name)

        if m:
            return True
        else:
            return False

    def start(self):
        """開始ボタン押下時の処理"""

        # crawlerモジュールに出力先のファイルパスを渡す
        self.crawler.output_path = self.output_path_var.get()

        # crawlerモジュールにおけるスレッド作成/開始の関数
        # 呼び出すたびに新たなスレッドが作成されるので、GUIを閉じずに連続実行が可能
        self.crawler.start_crawler_thread()

        # ボタンの状態とメッセージ更新
        self.start_btn.config(state='disabled')
        self.pause_btn.config(state='normal')
        self.cancel_btn.config(state='normal')
        self.clear_btn.config(state='disabled')
        self.file_dialog_btn.config(state='disabled')
        self.message_var.set('Crawler処理中...')
        self.message.config(fg='black')

        # 開始ボタンが押下された2秒後に指定された関数を呼び出す
        self.start_btn.after(2000, self.confirm_crawler_status)

    def confirm_crawler_status(self):
        """
        crawlerモジュールにおけるスレッドの状態を一定間隔で監視、
        その状態に応じてGUI等の初期化処理
        """

        # none(正常終了)、cancel(取消終了)を検知したらGUIの初期化関数を呼び出す
        if self.crawler.crawler_status == self.crawler.status[0] or \
                self.crawler.crawler_status == self.crawler.status[3]:

            # GUIの初期化関数
            self.initialize_gui_and_crawler()

            # 対象の処理が終了しても後述のafter関数により、この関数はループ処理され、
            # 大きな負荷にはならないが、念のため対象の処理終了に合わせて終了
            return None

        # 自分自身を指定しているため2秒間隔のループ処理となる
        self.start_btn.after(2000, self.confirm_crawler_status)

    def initialize_gui_and_crawler(self):
        """GUIのボタン等の状態とcrawlerモジュールの一部属性を初期化"""

        # crawlerモジュールの属性を初期化
        self.crawler.result_counter = {
            'Request sent count': 0,
            'Response received count': 0,
            'Status code count': defaultdict(int),
            'Scraped content count': 0,
        }

        # GUIのボタン等を初期化
        self.file_dialog_btn.config(state='normal')
        self.start_btn.config(state='normal')
        # disabled状態ではテキストを変更できないので順番に注意
        self.pause_btn.config(text='停止')
        self.pause_btn.config(state='disabled')
        self.cancel_btn.config(state='disabled')
        self.clear_btn.config(state='normal')

        # 出力ファイルパスの新規作成(更新)
        self.create_output_path()
        # 「ファイルの出力先」のエントリーも更新
        # GUIを閉じずに連続実行した場合の同名による上書きを防ぐ
        self.output_path_var.set(self.default_output_path)
        self.message_var.set('Crawler処理終了')

    def pause(self):
        """停止/再開ボタン押下時の処理"""

        # crawlerモジュールにおけるthreading.Eventの状態に応じた処理
        if self.crawler.crawler_event.is_set():
            # GUIからcrawlerモジュールのthreading.Eventを操作することで対象の処理を制御
            self.crawler.crawler_event.clear()
            self.pause_btn.config(text='再開')
            self.message_var.set('Crawler停止中')
        else:
            # GUIからcrawlerモジュールのthreading.Eventを操作することで対象の処理を制御
            self.crawler.crawler_event.set()
            self.pause_btn.config(text='停止')
            self.message_var.set('Crawler処理中...')

    def cancel(self):
        """取消ボタン押下時の処理"""

        # メッセージボックスによる確認、結果が返ってくるまで処理を停止
        # GUIからcrawlerモジュールのthreading.Eventを操作することで対象の処理を制御
        self.crawler.crawler_event.clear()

        # okボタンが押されらTrue、cancelボタンや✕ボタンが押されたらFalseが返る
        ask_result = messagebox.askokcancel(
            '確認',
            'Crawlerの処理を取消しますか？\n'
            '処理の途中で取消す場合、jsonファイルは出力されません。\n '
        )

        # 確認の結果に応じた処理
        if ask_result:
            # crawler側のeventとフラグを操作することで処理を終了(詳細はcrawler側の処理を参照)
            self.crawler.crawler_event.set()
            self.crawler.crawler_alive_flag = False
            # 念のためjoinによりスレッド終了まで待機
            self.crawler.crawler_thread.join()
        else:
            # 確認の結果、取り消さない場合は処理を再開
            # ただし、メッセージボックスをcancelや✕で閉じた場合、無条件で再開してしまうため、、
            # 停止ボタン以外のボタンで停止されている場合に限り、メッセージボックスを閉じた際に再開
            if self.pause_btn['text'] == '停止':
                self.crawler.crawler_event.set()

    def clear_log(self):
        """ログクリアボタン押下時の処理"""

        ask_result = messagebox.askokcancel(
            '確認',
            'ログウィンドウの表示内容をクリアしますか？'
        )

        if ask_result:
            # 初期状態がdisabledのため一度normalに戻す
            self.scrolled_text.config(state='normal')
            self.scrolled_text.delete(1.0, tk.END)
            self.scrolled_text.config(state='disabled')

    def quit(self):
        """終了ボタン押下時の処理"""

        # crawlerモジュールの対象処理の状態に応じた処理
        # 処理中や処理停止中の場合は、メッセージボックスにより確認、結果が返ってくるまで処理を停止
        # 反対に、初期状態や処理終了後は、確認の必要はないものとしてメッセージボックスを表示せずに終了
        if self.crawler.crawler_status == self.crawler.status[1] or \
                self.crawler.crawler_status == self.crawler.status[2]:

            # GUIからcrawlerモジュールのthreading.Eventを操作することで対象の処理を制御
            self.crawler.crawler_event.clear()

            # okボタンが押されらTrue、cancelボタンや✕ボタンが押されたらFalse
            ask_result = messagebox.askokcancel(
                '確認',
                'アプリを終了しますか？\n'
                '処理の途中で終了する場合、jsonファイルは出力されません。\n '
            )

            # 確認結果に応じた処理
            if ask_result:
                # GUIからcrawlerモジュールのthreading.Eventとフラグを操作することで対象の処理を制御
                self.crawler.crawler_event.set()
                self.crawler.crawler_alive_flag = False
                # 念のためjoinによりスレッド終了まで待機
                self.crawler.crawler_thread.join()
                self.master.destroy()
            else:
                # 確認の結果、取消さない場合は処理を再開
                # ただし、メッセージボックスをcancelや✕で閉じた場合、無条件で再開してしまうため、、
                # 停止ボタン以外のボタンで停止されている場合に限り、メッセージボックスを閉じた際に再開
                # 処理停止中で、ボタンテキストが「停止」の場合、停止ボタン以外での停止と判断
                if self.pause_btn['text'] == '停止':
                    self.crawler.crawler_event.set()
        # 初期状態や処理終了後は、確認の必要はないものとしてメッセージボックスを表示せずに終了
        else:
            self.master.destroy()


class LogWindowUi(object):
    """ログウィンドウ部分における各widget/機能の定義"""

    def __init__(self, frame, crawler):
        # Appクラスで定義したログウィンドウ用のラベルフレーム
        self.frame = frame
        # Appクラスでインスタンス化されたcrawlerモジュールを属性として定義
        self.crawler = crawler
        # crawlerモジュールで定義されたログ出力用のQueue(widgetに表示するログを取り出すため)
        self.log_queue = self.crawler.log_queue
        # crawlerモジュールで定義されたQueueHandler(取り出したログにフォーマットを適用させるため)
        self.queue_handler = self.crawler.queue_handler

        # ログ表示用のscrolledtextを定義
        self.scrolled_text = ScrolledText(
            self.frame,
            height=16,
            state='disabled',
        )
        self.scrolled_text.grid(column=0, row=0, sticky='nesw')

        # タグに応じた文字色を設定
        # タグは、scrolledtextにテキスト情報をinsertする際に設定
        self.scrolled_text.tag_config('ERROR', foreground='red')

        # ログウィンドウが読み込まれた0.1秒後に指定された関数を呼び出す
        self.frame.after(100, self.get_log_queue)

    def get_log_queue(self):
        """
        crawlerモジュールにおけるQueueのログ格納状況を監視/取り出し、
        scrolledtextへの表示関数の呼び出し等をGUIが終了するまで一定間隔で実行
        """

        while True:
            # crawlerモジュールのQueueからログを取り出せたら変数に格納
            try:
                record = self.log_queue.get(block=False)
            # 取り出せない場合はwhileループから抜ける
            except queue.Empty:
                break
            else:
                # 取り出せた場合はさらにログを引数に表示処理の関数を呼び出す
                self.display_log(record)

        # ログがある場合は取り出して関数呼び出し、ログがない場合はwhileループから抜けるが、
        # 以下のafter関数により再度whileループを実行することで、GUIが終了するまで上記の処理をループ
        self.frame.after(100, self.get_log_queue)

    def display_log(self, record):
        """crawlerモジュールのQueueから取り出したログをscrolledtextに表示"""

        # テキストをinsertする前に一度normalに変更
        self.scrolled_text.configure(state='normal')
        # format関数によりQueueから取り出したログに、crawlerモジュールのformatterを適用
        # また、同関数によりLogRecordオブジェクトからstr型に変換され、scrolledtextへのinsertが可能
        message = self.queue_handler.format(record)
        # タグ情報としてログレベルを渡すことで、引数で受け取ったログのレベルに応じたタグを設定
        self.scrolled_text.insert(tk.END, message + '\n', record.levelname)
        # insertが終わったら再びdisabledに変更
        self.scrolled_text.configure(state='disabled')
        # 呼び出し元はループ処理で、ログを取り出す度にこの関数を呼び出すため、
        # ログを表示させるたびに末尾までスクロールして、オートスクロールのように動作
        self.scrolled_text.yview(tk.END)


class App(object):
    """
    GUIの全体管理

    Note
        全体のレイアウトイメージとして、上部にCrawlerコントロール、下部にログウィンドウを表示
        縦方向のPanedWindowを土台として、その上にLabelFrameを配置して区切り、その上にそれぞれのwidgetを配置
    """

    def __init__(self, master):
        self.master = master
        # row/columnconfigureのweightをデフォルトの0(伸縮しない)から変更することで、
        # windowの伸縮に合わせて、設定された比率に応じて内部widget(ここではLabelFrame)も伸縮
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)

        # crawlerモジュールのインスタンス化
        crawler = Crawler()

        # 初めに、全体の土台として、master上に縦方向のPanedWindowをgrid配置
        vertical_pane = ttk.PanedWindow(master, orient='vertical')
        vertical_pane.grid(column=0, row=0, sticky='nesw')

        # Crawlerコントロールの土台となるLabelFrameを定義
        control_frame = ttk.LabelFrame(vertical_pane, text='Crawlerコントロール')
        # これを(master上に配置した)vertical_paneにadd
        vertical_pane.add(control_frame, weight=1)

        # ログウィンドウの土台となるLabelFrameを定義
        # 後に配置するscrolledtextもLabelFrameの伸縮に合わせて伸縮させるため、row/columnconfigureを設定
        # masterのconfigureや以下のconfigureをコメントアウトして実際に伸縮させるとわかりやすい
        log_window_frame = ttk.LabelFrame(vertical_pane, text='ログウィンドウ')
        log_window_frame.columnconfigure(0, weight=1)
        log_window_frame.rowconfigure(0, weight=1)
        # これを(master上に配置した)vertical_paneにadd
        vertical_pane.add(log_window_frame, weight=1)

        # 上記のLabelFrame等を引数に渡し、各レイアウト部分を定義したクラスをインスタンス化
        self.log_window = LogWindowUi(log_window_frame, crawler)
        self.control = ControlUi(
            control_frame, crawler, master, self.log_window)

        # ウィンドウの✕ボタンの処理(WM_DELETE_WINDOW)をControlUiクラスの関数に置き換える
        master.protocol('WM_DELETE_WINDOW', self.control.quit)


def main():
    root = tk.Tk()
    root.title('Crawler GUI')
    root.minsize(width=600, height=550)
    root.geometry('600x500')
    root.iconbitmap('./icon.ico')
    # AppクラスにTkオブジェクト(root)を渡してインスタンス化、
    # 同クラス内では、さらに各レイアウト部分を定義したクラスをインスタンス化、
    # そのオブジェクトを以降のmainloopよりGUIとして表示
    app = App(master=root)
    app.master.mainloop()


if __name__ == '__main__':
    main()
