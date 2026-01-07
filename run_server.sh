#!/bin/bash
# Startup script for vulnerability management system

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}脆弱性管理システム起動スクリプト${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}仮想環境が見つかりません。作成します...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}仮想環境の作成に失敗しました。${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${YELLOW}仮想環境をアクティブ化しています...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}依存関係をインストールしています...${NC}"
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}依存関係のインストールに失敗しました。${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}.envファイルが見つかりません。.env.exampleからコピーします...${NC}"
    cp .env.example .env
fi

# Start the server
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}サーバーを起動しています...${NC}"
echo -e "${GREEN}アクセスURL: http://localhost:8347${NC}"
echo -e "${GREEN}API Docs: http://localhost:8347/api/docs${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8347 --reload
