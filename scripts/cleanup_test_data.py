#!/usr/bin/env python3
"""
テストレコードを削除するスクリプト
Neonデータベースから、テストで作成された脆弱性データを削除します。
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# .envファイルを読み込み
env_path = project_root / '.env'
load_dotenv(env_path, override=True)

from sqlalchemy import create_engine, text
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def delete_test_data():
    """テストデータを削除"""
    # Neonの接続文字列
    neon_db_url = os.getenv('DATABASE_URL')
    if not neon_db_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    logger.info(f"Neonデータベースに接続: {neon_db_url.split('@')[1] if '@' in neon_db_url else 'local'}")

    try:
        # Neonエンジン作成
        engine = create_engine(neon_db_url)

        with engine.connect() as conn:
            # テストレコード確認
            logger.info("テストレコードを検索中...")

            # パターン1: タイトルに "Test" を含む
            result = conn.execute(text("""
                SELECT cve_id, title, published_date
                FROM vulnerabilities
                WHERE title LIKE '%Test%' OR title LIKE '%test%'
                ORDER BY published_date DESC
            """))
            test_records = result.fetchall()

            if len(test_records) == 0:
                logger.info("✅ テストレコードは見つかりませんでした")
                return

            logger.info(f"削除対象: {len(test_records)}件のテストレコード")
            logger.info("--- 削除対象レコード ---")
            for record in test_records[:10]:  # 最初の10件を表示
                logger.info(f"  - {record[0]}: {record[1]} (公開日: {record[2]})")

            if len(test_records) > 10:
                logger.info(f"  ... 他 {len(test_records) - 10}件")

            # 削除実行
            logger.info("テストレコードを削除中...")
            result = conn.execute(text("""
                DELETE FROM vulnerabilities
                WHERE title LIKE '%Test%' OR title LIKE '%test%'
            """))
            deleted_count = result.rowcount
            conn.commit()
            logger.info(f"✅ 削除完了: {deleted_count}件")

        # 最終確認
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM vulnerabilities"))
            total_count = result.scalar()
            logger.info(f"残りのレコード数: {total_count}件")

    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        raise


def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("テストデータ削除スクリプト")
    logger.info("=" * 60)

    delete_test_data()

    logger.info("\n" + "=" * 60)
    logger.info("✅ クリーンアップ完了！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
