# 2foods 見積書作成アプリ（Streamlit版）

## 概要
営業チーム向けの見積書作成アプリです。
- 商品を選択して見積書PDFを生成
- 見積履歴をアプリ内データベース（SQLite）で管理
- 過去の見積を検索・再ダウンロード可能

---

## 初回セットアップ手順

### Step 1: このフォルダを開く
エクスプローラーで以下のフォルダを開きます：
```
G:\共有ドライブ\TWO\2foods\04_Strategic Sales\90_Sales\2Snack\00_全体ファイル\見積書アプリ_streamlit
```

### Step 2: コマンドプロンプトを開く
1. エクスプローラーのアドレスバーに `cmd` と入力してEnter
2. または、フォルダ内で Shift + 右クリック → 「ここでコマンドウィンドウを開く」

### Step 3: 必要ライブラリをインストール
以下のコマンドを実行：
```bash
pip install -r requirements.txt
```

### Step 4: アプリを起動
```bash
streamlit run app.py
```

### Step 5: ブラウザで操作
自動的にブラウザが開きます（開かない場合は http://localhost:8501 にアクセス）

---

## 使い方

### 見積書作成
1. サイドバーで「見積書作成」を選択
2. 基本情報を入力（送付先、対象小売名、担当者、日付、販売エリア）
3. 商品を選択（チェックボックスで選択、卸価格・特別条件を入力）
4. 備考を設定
5. 「見積書を作成」ボタンをクリック
6. 「PDFダウンロード」ボタンからダウンロード

### 見積履歴
1. サイドバーで「見積履歴」を選択
2. 検索・フィルターで絞り込み
3. 展開して詳細を確認
4. 「PDF再生成」で過去の見積をダウンロード

---

## ファイル構成

```
見積書アプリ_streamlit/
├── app.py              # メインアプリ
├── products.py         # 商品マスタ
├── database.py         # データベース管理
├── pdf_generator.py    # PDF生成
├── requirements.txt    # 必要ライブラリ
├── quote_history.db    # 見積履歴DB（自動生成）
└── README.md           # この説明書
```

---

## トラブルシューティング

### Q: `streamlit` コマンドが見つからない
```bash
python -m streamlit run app.py
```
または
```bash
py -m streamlit run app.py
```

### Q: ライブラリのインストールエラー
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Q: 文字化け・フォントの問題
PDF内の日本語が表示されない場合、Windowsの日本語フォント（メイリオ等）が必要です。

---

## Streamlit Cloud へのデプロイ（オプション）

1. GitHubリポジトリにこのフォルダをプッシュ
2. https://share.streamlit.io/ にアクセス
3. 「New app」→ リポジトリを選択 → `app.py` を指定
4. 「Deploy」

※共有ドライブのパスはCloud環境では使用できないため、別途調整が必要です。
