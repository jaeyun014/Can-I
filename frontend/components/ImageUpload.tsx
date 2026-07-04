"use client";

import { Camera, ImagePlus, Upload, X } from "lucide-react";
import { useEffect, useState } from "react";

type Props = {
  file: File | null;
  onChange: (file: File | null) => void;
};

export function ImageUpload({ file, onChange }: Props) {
  const [preview, setPreview] = useState<string>("");

  useEffect(() => {
    if (!file) {
      setPreview("");
      return;
    }
    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  function handleImage(fileList: FileList | null) {
    const selectedFile = fileList?.[0];
    if (!selectedFile) {
      return;
    }
    onChange(selectedFile);
  }

  return (
    <div className="space-y-3">
      <div className="flex h-44 flex-col items-center justify-center rounded-lg border border-dashed border-stone-300 bg-white/80 text-center">
        {preview ? (
          <img src={preview} alt="선택된 이미지 미리보기" className="h-full w-full rounded-lg object-cover" />
        ) : (
          <>
            <ImagePlus className="mb-2 h-8 w-8 text-mint" aria-hidden />
            <span className="text-sm font-semibold text-ink">사진 선택</span>
            <span className="mt-1 text-xs text-stone-500">이미지는 현재 stub 분석으로 처리됩니다.</span>
          </>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <label className="inline-flex h-11 cursor-pointer items-center justify-center gap-2 rounded-md border border-stone-300 bg-white px-3 text-sm font-bold text-stone-700 transition hover:border-mint hover:text-mint">
          <Upload className="h-4 w-4" aria-hidden />
          파일 선택
          <input
            className="sr-only"
            type="file"
            accept="image/*"
            onChange={(event) => handleImage(event.target.files)}
          />
        </label>

        <label className="inline-flex h-11 cursor-pointer items-center justify-center gap-2 rounded-md border border-stone-300 bg-white px-3 text-sm font-bold text-stone-700 transition hover:border-mint hover:text-mint">
          <Camera className="h-4 w-4" aria-hidden />
          사진 촬영
          <input
            className="sr-only"
            type="file"
            accept="image/*"
            capture="environment"
            onChange={(event) => handleImage(event.target.files)}
          />
        </label>
      </div>

      {file ? (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="max-w-full truncate text-xs text-stone-500">{file.name}</p>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-md border border-stone-300 bg-white px-3 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
            onClick={() => onChange(null)}
          >
            <X className="h-4 w-4" aria-hidden />
            사진 제거
          </button>
        </div>
      ) : null}
    </div>
  );
}
