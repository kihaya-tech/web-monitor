# Website Monitor Bot

[English](README.md) | **日本語**

---

複数のWebサイトを監視し、変更があった際にDiscordに通知するPythonベースのボットです。GitHub Actionsで定期的に実行されます。

## 機能

- 複数のWebサイトを同時に監視
- コンテンツの変更を自動検出（SHA-256ハッシュベース）
- Discord Webhookを通じてリアルタイム通知
- GitHub Actionsで自動実行（デフォルト: 1時間ごと）
- セキュアな設定（秘密情報はGitHub Secretsで管理）
- CSSセレクタによる部分監視対応

## プロジェクト構造

```
monitor-web/
├── .github/
│   └── workflows/
│       └── monitor.yml       # GitHub Actions workflow
├── src/
│   └── monitor.py            # Main monitoring script
├── config/
│   └── sites.json            # Site configuration file
├── data/
│   ├── .gitkeep
│   └── *.json                # State files (auto-generated)
├── requirements.txt          # Python dependencies
├── .gitignore
└── README.md
```

## セットアップ

### 1. リポジトリのセットアップ

1. このリポジトリをGitHubにプッシュ
2. リポジトリの設定でGitHub Actionsを有効化
3. Workflow permissionsを設定（重要）

#### Workflow Permissions設定

リポジトリ Settings → Actions → General → Workflow permissions:
- **"Read and write permissions"** を選択
- "Allow GitHub Actions to create and approve pull requests" にチェック（オプション）

この設定がないと、状態ファイルのコミットに失敗します。

### 2. Discord Webhookの設定

1. Discordサーバーの設定 → 連携サービス → Webhook
2. 新しいWebhookを作成し、URLをコピー
3. GitHubリポジトリの Settings → Secrets and variables → Actions
4. New repository secret をクリック
5. Name: `DISCORD_WEBHOOK_URL`
6. Value: コピーしたWebhook URL

### 3. 監視サイトの設定

`config/sites.json` を編集して、監視したいサイトを追加:

```json
[
  {
    "name": "Example Site",
    "url": "https://example.com",
    "selector": "body",
    "check_interval": "hourly"
  },
  {
    "name": "Another Site",
    "url": "https://example.org/page",
    "selector": "main .content",
    "check_interval": "hourly"
  }
]
```

#### 設定パラメータ詳細

##### `name` (string, required)
- サイトの識別名
- Discord通知のタイトルに使用される
- 状態ファイル名の生成に使用される（英数字以外は `_` に変換される）

##### `url` (string, required)
- 監視するWebサイトのURL
- HTTP/HTTPS両方サポート（HTTPSを推奨）
- クエリパラメータやフラグメント識別子も含められる
- 例: `https://example.com/page?id=123#section`

##### `selector` (string, optional)
- 監視対象を絞り込むためのCSSセレクタ
- デフォルト: `"body"` (ページ全体)
- BeautifulSoup4のCSS Selector記法に従う
- 複雑なセレクタも使用可能

**セレクタの例:**
```json
"selector": "body"                          // ページ全体
"selector": ".content"                      // class="content"
"selector": "#main-content"                 // id="main-content"
"selector": "article.post"                  // <article class="post">
"selector": "div.container > p"             // 直接の子要素
"selector": ".news-list li:first-child"     // 擬似クラス
"selector": "[data-id='123']"               // 属性セレクタ
```

##### `check_interval` (string, currently unused)
- **現在のバージョンでは未実装**
- 将来の拡張のために予約されたフィールド
- 現在は全サイトが同時にチェックされる
- 実際のチェック頻度はGitHub ActionsのcronスケジュールでGLOBALに制御される

**注意:** `check_interval`フィールドはJSONに記述できますが、現在のところ実装では使用されていません。すべてのサイトは`.github/workflows/monitor.yml`で設定されたスケジュールに従って同時にチェックされます。

**想定される将来の値（未実装）:**
- `"realtime"` - 可能な限り頻繁にチェック
- `"hourly"` - 1時間ごと
- `"daily"` - 1日1回
- `"custom"` - カスタムスケジュール

### 4. 実行スケジュールの設定

`.github/workflows/monitor.yml` でチェック頻度を設定します。これがシステム全体の実行頻度を決定します。

```yaml
on:
  schedule:
    - cron: '0 * * * *'  # Every hour
```

#### Cron構文の詳細

```
┌───────────── 分 (0 - 59)
│ ┌───────────── 時 (0 - 23)
│ │ ┌───────────── 日 (1 - 31)
│ │ │ ┌───────────── 月 (1 - 12)
│ │ │ │ ┌───────────── 曜日 (0 - 7) (0と7は日曜日)
│ │ │ │ │
* * * * *
```

#### よく使うパターン

```yaml
# 1時間ごと
- cron: '0 * * * *'

# 30分ごと
- cron: '*/30 * * * *'

# 15分ごと
- cron: '*/15 * * * *'

# 6時間ごと（0時、6時、12時、18時）
- cron: '0 */6 * * *'

# 毎日午前9時（UTC）
- cron: '0 9 * * *'

# 毎日午前0時（UTC）= 日本時間午前9時
- cron: '0 0 * * *'

# 平日の午前9時（UTC）
- cron: '0 9 * * 1-5'

# 月曜日と金曜日の12時（UTC）
- cron: '0 12 * * 1,5'

# 毎月1日の午前0時（UTC）
- cron: '0 0 1 * *'
```

**注意事項:**
- GitHub ActionsのcronはUTC（協定世界時）で動作
- 日本時間（JST）はUTC+9時間
- 例: UTC 0時 = JST 9時
- GitHub Actionsのスケジュール実行は数分遅延する可能性がある
- 高頻度実行（5分未満）はGitHub Actionsの制約により推奨されない

#### トリガー条件の詳細

`monitor.yml`には複数のトリガー条件が設定されています:

```yaml
on:
  # 定期実行（メインの実行方法）
  schedule:
    - cron: '0 * * * *'

  # 手動実行（テスト用）
  workflow_dispatch:

  # コード変更時の実行（開発時のテスト用）
  push:
    branches:
      - main
    paths:
      - 'src/**'
      - 'config/**'
      - '.github/workflows/monitor.yml'
```

### 時間管理の仕組み: CronとJSONの関係

**重要な設計理解:**

このシステムでは、時間管理は**2つのレベル**で考えられていますが、**現在は1つだけが実装されています**。

#### レベル1: グローバルスケジュール（実装済み）
`.github/workflows/monitor.yml` のcron設定
- **役割**: GitHub Actionsがスクリプトを実行するタイミング
- **スコープ**: すべてのサイトに適用
- **制御方法**: cronスケジュール
- **例**: `cron: '0 * * * *'` → 1時間ごとにスクリプト実行

#### レベル2: サイト個別スケジュール（未実装）
`config/sites.json` の`check_interval`フィールド
- **役割**: 各サイトを個別のスケジュールでチェック
- **スコープ**: サイトごとに設定可能
- **現状**: フィールドは存在するが実装されていない
- **将来の実装案**: 最終チェック時刻を記録し、間隔に応じてスキップ

#### 現在の動作

```
GitHub Actions (cron: 毎時)
  ↓ スクリプト実行
  ↓
monitor.py起動
  ↓
全サイトを同時にチェック
  ├─ Site 1をチェック
  ├─ Site 2をチェック
  └─ Site 3をチェック
```

すべてのサイトは**同じタイミング**でチェックされます。`check_interval`フィールドの値（`"hourly"`など）は無視されます。

#### 将来の実装案（参考）

個別スケジュールを実装する場合の動作イメージ:

```python
# 疑似コード（未実装）
for site in sites:
    if should_check(site, last_check_time, site['check_interval']):
        check_site(site)
    else:
        skip_site(site)
```

この場合、cronは頻繁に実行し、各サイトは個別の`check_interval`に従ってチェックされる。

#### 推奨される使用方法

**現在のバージョンでは:**
1. すべてのサイトを同じ頻度でチェックしたい → cronのみ設定
2. 特定のサイトだけ頻繁にチェックしたい → 複数のワークフローを作成
3. サイトごとに異なる頻度 → 未サポート（将来の機能）

**例: 複数のワークフローで異なる頻度を実現**

`.github/workflows/monitor-hourly.yml`:
```yaml
name: Hourly Monitor
on:
  schedule:
    - cron: '0 * * * *'
env:
  CONFIG_PATH: config/sites-hourly.json
```

`.github/workflows/monitor-daily.yml`:
```yaml
name: Daily Monitor
on:
  schedule:
    - cron: '0 9 * * *'
env:
  CONFIG_PATH: config/sites-daily.json
```

## 使い方

### 自動実行

GitHub Actionsが設定したスケジュールで自動的に実行されます。

### 手動実行

GitHub リポジトリの Actions タブから:
1. "Website Monitor" ワークフローを選択
2. "Run workflow" をクリック
3. ブランチを選択（通常はmain）
4. "Run workflow" を再度クリック

### ローカルテスト

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
export DISCORD_WEBHOOK_URL="your_webhook_url_here"

# モニターの実行
python src/monitor.py

# カスタム設定ファイルを使用
export CONFIG_PATH="config/custom-sites.json"
export STATE_DIR="data/custom"
python src/monitor.py
```

Windows環境:
```cmd
pip install -r requirements.txt
set DISCORD_WEBHOOK_URL=your_webhook_url_here
python src/monitor.py
```

## 動作原理

### 実行フロー

1. **初期化**
   - 環境変数から`DISCORD_WEBHOOK_URL`を読み込み
   - `config/sites.json`から監視サイトリストを読み込み
   - `data/`ディレクトリの存在確認/作成

2. **各サイトのチェック**
   ```
   for each site in config:
     ├─ HTTPリクエストでコンテンツ取得
     ├─ BeautifulSoup4でHTML解析
     ├─ CSSセレクタで対象要素を抽出
     ├─ テキストコンテンツのみを取得
     ├─ SHA-256ハッシュ値を計算
     ├─ data/{site_name}.jsonから前回の状態を読み込み
     ├─ ハッシュ値を比較
     ├─ 変更検出時 → Discord通知送信
     └─ 現在の状態をdata/{site_name}.jsonに保存
   ```

3. **状態の永続化**
   - GitHub Actionsが`data/`ディレクトリの変更を自動コミット
   - 次回実行時に前回の状態を参照可能

### 変更検出の仕組み

#### SHA-256ハッシュベース検出
コンテンツ全体をSHA-256ハッシュ化し、前回との比較で変更を検出:

**メリット:**
- 高速（O(1)の比較）
- 軽量（64文字の文字列のみ保存）
- HTMLタグの変更も検出

**デメリット:**
- 1文字でも変わると検出される（広告の変更など）
- 何が変わったかはわからない（差分は取得しない）

#### 初回実行の挙動

```
1回目の実行:
├─ 状態ファイルが存在しない
├─ ハッシュ値を計算
├─ 状態ファイルに保存
└─ 通知は送信しない（初期化のみ）

2回目以降:
├─ 前回の状態ファイルを読み込み
├─ 現在のハッシュ値と比較
├─ 変更があれば通知送信
└─ 新しい状態を保存
```

### 状態ファイルの構造

`data/{sanitized_site_name}.json`:
```json
{
  "hash": "a3f5e8c...",
  "last_checked": "2025-10-30T12:34:56.789Z",
  "url": "https://example.com",
  "previous_hash": "b4e6f9d..."
}
```

**フィールド説明:**
- `hash`: 現在のコンテンツのSHA-256ハッシュ
- `last_checked`: 最終チェック日時（ISO 8601形式、UTC）
- `url`: 監視しているURL
- `previous_hash`: 前回のハッシュ（変更検出時のみ）

## Discord通知フォーマット

通知は以下の情報を含むEmbedとして送信されます:

```
🔔 Change Detected: {site_name}

Site: {site_name}
URL: {url}
Previous Hash: `abc123...`
New Hash: `def456...`

Timestamp: 2025-10-30T12:34:56.789Z
Footer: Website Monitor Bot
```

### 通知のカスタマイズ

`src/monitor.py`の`_send_discord_notification`メソッドを編集することで、通知内容を変更できます:

```python
embed = {
    "title": f"🔔 Change Detected: {site_name}",  # タイトル
    "url": url,                                    # クリック可能なURL
    "color": 3447003,                              # 色（10進数のRGB）
    "fields": [                                    # フィールド配列
        {
            "name": "Site",
            "value": site_name,
            "inline": True
        },
        # ... 追加フィールド
    ],
    "timestamp": datetime.utcnow().isoformat(),
    "footer": {
        "text": "Website Monitor Bot"
    }
}
```

**色の指定:**
- Blue (デフォルト): `3447003`
- Green: `3066993`
- Yellow: `16776960`
- Orange: `15105570`
- Red: `15158332`

## セキュリティ

### セキュアな設計

1. **Webhook URLの保護**
   - GitHub Secretsで暗号化保存
   - ログに出力されない
   - リポジトリをpublicにしても安全

2. **状態ファイルの安全性**
   - 機密情報は含まれない（ハッシュ値とURL、タイムスタンプのみ）
   - publicリポジトリでも問題なくコミット可能

3. **環境変数の使用**
   ```python
   self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
   ```
   ハードコードされた認証情報は存在しない

### GitHub Secretsの管理

- Repository Secrets: 単一リポジトリのみで使用
- Environment Secrets: 特定の環境（production, stagingなど）で使用
- Organization Secrets: 組織全体で共有

このプロジェクトではRepository Secretsを使用。

## 高度な設定

### 複数の設定ファイルを使用

環境変数でカスタム設定ファイルを指定:

```yaml
# .github/workflows/monitor-custom.yml
env:
  CONFIG_PATH: config/production-sites.json
  STATE_DIR: data/production
```

### タイムアウト設定

`src/monitor.py`の`_fetch_content`メソッド:
```python
response = requests.get(url, headers=headers, timeout=30)  # 30秒
```

サイトの応答が遅い場合、この値を調整。

### User-Agent設定

デフォルト:
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (compatible; WebsiteMonitorBot/1.0)'
}
```

一部のサイトではUser-Agentのブロックがあるため、必要に応じて変更。

### カスタムヘッダーの追加

```python
headers = {
    'User-Agent': 'Mozilla/5.0 ...',
    'Accept-Language': 'ja-JP,ja;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    # 必要に応じて追加
}
```

## 依存関係

`requirements.txt`:
```
requests==2.32.3      # HTTPクライアント
beautifulsoup4==4.12.3  # HTML解析
```

### バージョンの更新

```bash
# 最新バージョンを確認
pip list --outdated

# requirements.txtを更新
pip install --upgrade requests beautifulsoup4
pip freeze > requirements.txt
```

## トラブルシューティング

### Webhookが動作しない

**診断:**
```bash
# ローカルでテスト
export DISCORD_WEBHOOK_URL="your_webhook_url"
python src/monitor.py
```

**確認項目:**
- Discord Webhook URLが正しくSecretに設定されているか
- Webhookが削除されていないか
- Discordチャンネルのアクセス権限

### 通知が来ない

**原因1**: 初回実行
- 初回は状態の初期化のみ（通知なし）

**原因2**: サイトに変更がない
- 実際に変更が発生するまで待つ
- テスト: `config/sites.json`を変更してpush

**原因3**: GitHub Actionsのログでエラー
- Actions タブでログを確認

**原因4**: サイトが正常にアクセスできない
- ローカルで同じURLをテスト

### 権限エラー

```
! [remote rejected] main -> main (refusing to allow a GitHub App to create or update workflow `.github/workflows/monitor.yml` without `workflows` permission)
```

**解決方法:**
- Settings → Actions → General → Workflow permissions
- "Read and write permissions" を選択

### レート制限

GitHub Actionsで頻繁に実行しすぎるとレート制限に引っかかる可能性:

**制限:**
- スケジュール実行: 最短5分間隔を推奨
- 同時実行: デフォルトで20ジョブまで
- 実行時間: 1ジョブあたり最大6時間

**GitHub Actions無料枠:**
- Public repo: 無制限
- Private repo: 月2000分（無料アカウント）

### サイト取得失敗

**エラーメッセージ:**
```
Error fetching https://example.com: HTTPError 403 Forbidden
```

**原因と対策:**

1. **Bot保護 (403/429)**
   - User-Agentを変更
   - リクエスト頻度を下げる
   - そのサイトは監視不可能な場合もある

2. **タイムアウト (Timeout)**
   - `timeout`値を増やす（デフォルト30秒）
   ```python
   response = requests.get(url, headers=headers, timeout=60)
   ```

3. **DNS解決失敗**
   - URLのスペルミスを確認
   - サイトがダウンしている可能性

4. **SSL証明書エラー**
   ```python
   response = requests.get(url, headers=headers, verify=False)  # 非推奨
   ```

## パフォーマンス最適化

### 並列実行

現在は逐次実行。大量のサイトを監視する場合は並列化を検討:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(self.check_site, self.sites)
```

### キャッシュの活用

頻繁に変更されないサイトの場合、HTTPキャッシュヘッダーを利用:

```python
headers = {
    'Cache-Control': 'max-age=3600',
    'If-Modified-Since': last_modified,
}
```

## 制限事項

1. **JavaScript依存サイト**
   - SPAやJavaScriptでレンダリングされるコンテンツは取得できない
   - 解決策: Selenium/Puppeteerの導入が必要（未実装）

2. **認証が必要なサイト**
   - ログインが必要なページは監視できない
   - 解決策: セッション管理の実装が必要（未実装）

3. **差分の詳細**
   - 何が変わったかの詳細は取得しない
   - 解決策: diffライブラリの導入が必要（未実装）

4. **CAPTCHA対応サイト**
   - CAPTCHA保護されたサイトは監視できない

5. **レート制限**
   - アクセス頻度が高すぎるとIPブロックされる可能性
   - 推奨: 1サイトあたり5分以上の間隔

## 将来の拡張

1. **サイト個別スケジュール**
   - `check_interval`フィールドの実装
   - 各サイトを異なる頻度でチェック

2. **詳細な差分検出**
   - HTMLの差分を取得して通知
   - `difflib`ライブラリの使用

3. **複数の通知先**
   - Slack, Email, LINE, Telegram対応
   - 通知先を設定ファイルで選択可能

4. **JavaScript対応**
   - Selenium/Puppeteer統合
   - SPAサイトの監視対応

5. **スクリーンショット機能**
   - 変更前後のスクリーンショットを保存
   - Discordに画像添付

6. **Webダッシュボード**
   - 監視状況の可視化
   - 履歴の閲覧

## 貢献

Pull requests are welcome!

### 開発環境のセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/monitor-web.git
cd monitor-web

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 開発用の追加パッケージ
pip install pytest black flake8 mypy
```

### テスト

```bash
# ユニットテストの実行（未実装）
pytest tests/

# コードフォーマット
black src/

# Lint
flake8 src/

# 型チェック
mypy src/
```

## ライセンス

MIT License

## サポート

- バグ報告: GitHubのIssuesに投稿してください
- 質問: GitHubのDiscussionsに投稿してください
- 機能リクエスト: GitHubのIssuesに投稿してください

## 変更履歴

### v1.0.0 (Initial Release)
- 基本的な監視機能
- Discord通知
- GitHub Actions統合
- SHA-256ハッシュベースの変更検出
- CSSセレクタ対応
