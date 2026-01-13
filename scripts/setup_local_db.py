#!/usr/bin/env python3
"""
ローカルPostgreSQLにテーブルを作成し、Neonからデータをコピーするスクリプト
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# .envファイルを読み込み（既存の環境変数を上書き）
env_path = project_root / '.env'
load_dotenv(env_path, override=True)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.models.vulnerability import Base, Vulnerability
import logging
import json

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_local_tables():
    """ローカルPostgreSQLにテーブルを作成"""
    # ローカルPostgreSQLの接続文字列
    # Dockerコンテナ内からはコンテナ名で接続
    local_db_url = "postgresql://postgres:postgres@zjs_postgres:5432/vulnerabilities"

    logger.info(f"ローカルデータベースに接続: {local_db_url}")

    try:
        # エンジン作成
        engine = create_engine(local_db_url)

        # テーブル作成
        logger.info("テーブルを作成中...")
        Base.metadata.create_all(bind=engine)

        # テーブル確認
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result]
            logger.info(f"作成されたテーブル: {tables}")

        logger.info("✅ テーブル作成完了")
        return engine

    except Exception as e:
        logger.error(f"❌ テーブル作成失敗: {e}")
        raise


def copy_data_from_neon(local_engine):
    """NeonからローカルPostgreSQLにデータをコピー"""
    # Neonの接続文字列（.envから直接取得）
    neon_db_url = os.getenv('DATABASE_URL')
    if not neon_db_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    logger.info(f"Neonデータベースに接続: {neon_db_url.split('@')[1] if '@' in neon_db_url else 'local'}")  # パスワード部分を隠す

    try:
        # Neonエンジン作成
        neon_engine = create_engine(neon_db_url)

        # Neonからデータ取得
        logger.info("Neonからデータを取得中...")
        with neon_engine.connect() as neon_conn:
            result = neon_conn.execute(text("SELECT * FROM vulnerabilities ORDER BY created_at"))
            rows = result.fetchall()
            columns = result.keys()
            logger.info(f"取得件数: {len(rows)}件")

        if len(rows) == 0:
            logger.warning("⚠️  Neonにデータが存在しません")
            return

        # ローカルにデータ挿入
        logger.info("ローカルPostgreSQLにデータを挿入中...")
        with local_engine.connect() as local_conn:
            # トランザクション開始
            trans = local_conn.begin()
            try:
                # 既存データ削除（クリーンスタート）
                local_conn.execute(text("TRUNCATE TABLE vulnerabilities"))

                # データ挿入
                inserted = 0
                for row in rows:
                    # 辞書形式に変換
                    row_dict = dict(zip(columns, row))

                    # JSON/JSONBフィールドを文字列に変換
                    if row_dict.get('affected_products') and isinstance(row_dict['affected_products'], dict):
                        row_dict['affected_products'] = json.dumps(row_dict['affected_products'])
                    if row_dict.get('vendor_info') and isinstance(row_dict['vendor_info'], dict):
                        row_dict['vendor_info'] = json.dumps(row_dict['vendor_info'])
                    if row_dict.get('references') and isinstance(row_dict['references'], dict):
                        row_dict['references'] = json.dumps(row_dict['references'])

                    # INSERT文を構築（referencesは予約語なので引用符で囲む）
                    local_conn.execute(
                        text("""
                            INSERT INTO vulnerabilities (
                                cve_id, title, description, cvss_score, severity,
                                published_date, modified_date, affected_products,
                                vendor_info, "references", created_at, updated_at
                            ) VALUES (
                                :cve_id, :title, :description, :cvss_score, :severity,
                                :published_date, :modified_date,
                                CAST(:affected_products AS jsonb),
                                CAST(:vendor_info AS jsonb),
                                CAST(:references AS jsonb),
                                :created_at, :updated_at
                            )
                        """),
                        row_dict
                    )
                    inserted += 1

                    # 進捗表示（100件ごと）
                    if inserted % 100 == 0:
                        logger.info(f"  {inserted}/{len(rows)}件 挿入完了")

                # コミット
                trans.commit()
                logger.info(f"✅ データコピー完了: {inserted}件")

            except Exception as e:
                trans.rollback()
                logger.error(f"❌ データ挿入失敗（ロールバック）: {e}")
                raise

        # データ件数確認
        with local_engine.connect() as local_conn:
            result = local_conn.execute(text("SELECT COUNT(*) FROM vulnerabilities"))
            count = result.scalar()
            logger.info(f"ローカルDB総件数: {count}件")

    except Exception as e:
        logger.error(f"❌ データコピー失敗: {e}")
        raise


def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("ローカルPostgreSQLセットアップスクリプト")
    logger.info("=" * 60)

    # 手順1: テーブル作成
    logger.info("\n[手順1] ローカルPostgreSQLにテーブルを作成")
    local_engine = create_local_tables()

    # 手順2: データコピー
    logger.info("\n[手順2] NeonからローカルPostgreSQLにデータをコピー")
    copy_data_from_neon(local_engine)

    logger.info("\n" + "=" * 60)
    logger.info("✅ セットアップ完了！")
    logger.info("=" * 60)
    logger.info("次のコマンドで確認できます:")
    logger.info("  docker exec zjs_postgres psql -U postgres -d vulnerabilities -c 'SELECT COUNT(*) FROM vulnerabilities;'")


if __name__ == "__main__":
    main()
