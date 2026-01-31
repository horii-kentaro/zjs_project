# テスト用Dockerfile（意図的に脆弱性のあるバージョンを含む）
# セキュリティテスト・脆弱性検出機能のテスト用

# 古いバージョンのNode.js（CVE-2021-22930等の脆弱性あり）
FROM node:12.22.1-alpine3.12

# 古いバージョンのnginx（複数のCVEあり）
# FROM nginx:1.18.0-alpine

# システムパッケージのインストール（古いバージョン）
RUN apk add --no-cache \
    curl=7.67.0-r0 \
    openssl=1.1.1g-r0 \
    git=2.24.3-r0 \
    bash=5.0.11-r1

# アプリケーションディレクトリ
WORKDIR /app

# パッケージファイルをコピー
COPY package.json ./

# 依存関係のインストール（脆弱性のあるバージョン）
RUN npm install

# アプリケーションファイルをコピー
COPY . .

# ポート公開
EXPOSE 3000

# アプリケーション起動
CMD ["node", "index.js"]
