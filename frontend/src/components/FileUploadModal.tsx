import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { X, Upload, File as FileIcon, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from './ui/Button';
import type { FileImportResponse } from '../types';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File) => Promise<FileImportResponse>;
  uploadType: 'composer' | 'npm' | 'docker' | null;
  isUploading?: boolean;
}

export function FileUploadModal({ isOpen, onClose, onUpload, uploadType, isUploading }: FileUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<FileImportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ファイルタイプごとの設定
  const config = {
    composer: {
      title: 'Composerファイルのアップロード',
      hint: 'composer.json または composer.lock',
      accept: { 'application/json': ['.json', '.lock'] },
    },
    npm: {
      title: 'NPMファイルのアップロード',
      hint: 'package.json または package-lock.json',
      accept: { 'application/json': ['.json'] },
    },
    docker: {
      title: 'Dockerfileのアップロード',
      hint: 'Dockerfile（拡張子なし）',
      accept: undefined, // Dockerfileは拡張子がないため、すべてのファイルを受け入れる
    },
  };

  const currentConfig = uploadType ? config[uploadType] : null;

  // ドラッグ&ドロップハンドラー
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
      setError(null);
      setUploadResult(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    accept: currentConfig?.accept,
  });

  // アップロード実行
  const handleUpload = async () => {
    if (!selectedFile) {
      setError('ファイルを選択してください');
      return;
    }

    try {
      setError(null);
      const result = await onUpload(selectedFile);
      setUploadResult(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '不明なエラー';
      setError(`アップロードに失敗しました: ${errorMessage}`);
    }
  };

  // モーダルを閉じる
  const handleClose = () => {
    setSelectedFile(null);
    setUploadResult(null);
    setError(null);
    onClose();
  };

  if (!isOpen || !currentConfig) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-crust/80 backdrop-blur-sm">
      <div className="bg-base border border-surface-1 rounded-lg shadow-lg w-full max-w-md">
        {/* ヘッダー */}
        <div className="flex items-center justify-between p-4 border-b border-surface-1">
          <h2 className="text-xl font-bold text-text">{currentConfig.title}</h2>
          <button
            onClick={handleClose}
            className="text-subtext-0 hover:text-text transition-colors"
            disabled={isUploading}
          >
            <X size={24} />
          </button>
        </div>

        {/* コンテンツ */}
        <div className="p-4 space-y-4">
          {/* ヒント */}
          <p className="text-sm text-subtext-0">{currentConfig.hint}</p>

          {/* ドロップゾーン */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-blue bg-blue/10'
                : 'border-surface-2 hover:border-blue hover:bg-surface-0'
            }`}
          >
            <input {...getInputProps()} disabled={isUploading} />
            <div className="flex flex-col items-center gap-3">
              {selectedFile ? (
                <>
                  <FileIcon className="text-blue" size={48} />
                  <p className="text-text font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-subtext-0">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                </>
              ) : (
                <>
                  <Upload className="text-subtext-0" size={48} />
                  <div>
                    <p className="text-text font-medium">ファイルをドラッグ&ドロップ</p>
                    <p className="text-sm text-subtext-0">または クリックして選択</p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* 成功メッセージ */}
          {uploadResult && (
            <div className="bg-green/20 border border-green/30 rounded-lg p-4 flex items-start gap-3">
              <CheckCircle className="text-green flex-shrink-0" size={20} />
              <div className="flex-1">
                <p className="text-green text-sm font-medium">アップロード完了</p>
                <p className="text-green text-sm mt-1">
                  {uploadResult.imported_count}件の資産を登録しました
                  {uploadResult.skipped_count > 0 && ` (スキップ: ${uploadResult.skipped_count}件)`}
                </p>
                {uploadResult.errors && uploadResult.errors.length > 0 && (
                  <div className="mt-2 space-y-1">
                    <p className="text-red text-xs font-medium">エラー:</p>
                    {uploadResult.errors.slice(0, 3).map((err, index) => (
                      <p key={index} className="text-red text-xs">• {err}</p>
                    ))}
                    {uploadResult.errors.length > 3 && (
                      <p className="text-red text-xs">... 他 {uploadResult.errors.length - 3}件</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* エラーメッセージ */}
          {error && (
            <div className="bg-red/20 border border-red/30 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="text-red flex-shrink-0" size={20} />
              <p className="text-red text-sm">{error}</p>
            </div>
          )}

          {/* アクションボタン */}
          <div className="flex gap-2 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={handleClose}
              className="flex-1"
              disabled={isUploading}
            >
              {uploadResult ? '閉じる' : 'キャンセル'}
            </Button>
            {!uploadResult && (
              <Button
                type="button"
                variant="primary"
                onClick={handleUpload}
                className="flex-1"
                isLoading={isUploading}
                disabled={!selectedFile || isUploading}
              >
                <Upload size={16} />
                アップロード
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
