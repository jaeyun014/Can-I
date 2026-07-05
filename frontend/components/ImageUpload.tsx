"use client";

import { Camera, ImagePlus, Upload, X } from "lucide-react";
import { useEffect, useState } from "react";

type Props = {
  files: File[];
  onChange: (files: File[]) => void;
};

const shotLabels = ["전체 사진", "재질 코드", "안전 표기/바코드"];

export function ImageUpload({ files, onChange }: Props) {
  const [previews, setPreviews] = useState<string[]>([]);

  useEffect(() => {
    if (!files.length) {
      setPreviews([]);
      return;
    }
    const objectUrls = files.map((file) => URL.createObjectURL(file));
    setPreviews(objectUrls);
    return () => objectUrls.forEach((url) => URL.revokeObjectURL(url));
  }, [files]);

  function handleImage(fileList: FileList | null) {
    const selectedFiles = Array.from(fileList ?? []).filter((file) => file.type.startsWith("image/"));
    if (!selectedFiles.length) {
      return;
    }
    onChange([...files, ...selectedFiles].slice(0, 3));
  }

  function removeAt(index: number) {
    onChange(files.filter((_, fileIndex) => fileIndex !== index));
  }

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-dashed border-stone-300 bg-white/80 p-3 text-center">
        {previews.length ? (
          <div className="grid gap-3">
            {previews.map((preview, index) => (
              <div key={preview} className="overflow-hidden rounded-md border border-stone-200 bg-white text-left">
                <div className="relative aspect-[4/3]">
                  <img src={preview} alt={`${shotLabels[index] ?? "추가 사진"} 미리보기`} className="h-full w-full object-cover" />
                  <span className="absolute left-2 top-2 rounded-full bg-white/90 px-2 py-1 text-xs font-bold text-ink shadow-sm">
                    {index + 1}. {shotLabels[index] ?? "추가 사진"}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-2 p-2">
                  <p className="truncate text-xs text-stone-500">{files[index]?.name}</p>
                  <button
                    type="button"
                    className="inline-flex h-8 items-center gap-1 rounded-md border border-stone-300 bg-white px-2 text-xs font-semibold text-stone-700 hover:bg-stone-50"
                    onClick={() => removeAt(index)}
                  >
                    <X className="h-3.5 w-3.5" aria-hidden />
                    제거
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex h-56 flex-col items-center justify-center md:h-64">
            <ImagePlus className="mb-3 h-10 w-10 text-mint" aria-hidden />
            <span className="text-base font-bold text-ink">사진을 찍거나 이미지를 선택하세요</span>
            <span className="mt-1 text-xs text-stone-500">전체, 재질 코드, 안전 표기 사진을 함께 넣으면 더 정확합니다.</span>
          </div>
        )}
      </div>

      <div className="grid gap-2 rounded-md bg-stone-50 p-3 text-xs leading-5 text-stone-600">
        {shotLabels.map((label, index) => (
          <div key={label} className="flex items-center justify-between gap-2">
            <span>{index + 1}. {label}</span>
            <span className={`font-bold ${files[index] ? "text-mint" : "text-stone-400"}`}>{files[index] ? "추가됨" : "권장"}</span>
          </div>
        ))}
      </div>

      <div className="grid gap-3">
        <label className="inline-flex h-14 cursor-pointer items-center justify-center gap-3 rounded-md bg-ink px-4 text-base font-black text-white transition hover:bg-mint">
          <Camera className="h-6 w-6" aria-hidden />
          사진 촬영
          <input
            className="sr-only"
            type="file"
            accept="image/*"
            capture="environment"
            multiple
            onChange={(event) => handleImage(event.target.files)}
          />
        </label>

        <label className="inline-flex h-11 cursor-pointer items-center justify-center gap-2 rounded-md border border-stone-300 bg-white px-3 text-sm font-bold text-stone-700 transition hover:border-mint hover:text-mint">
          <Upload className="h-4 w-4" aria-hidden />
          파일 선택
          <input
            className="sr-only"
            type="file"
            accept="image/*"
            multiple
            onChange={(event) => handleImage(event.target.files)}
          />
        </label>
      </div>

      {files.length ? (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="max-w-full truncate text-xs text-stone-500">{files.length}장 선택됨</p>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-md border border-stone-300 bg-white px-3 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
            onClick={() => onChange([])}
          >
            <X className="h-4 w-4" aria-hidden />
            전체 제거
          </button>
        </div>
      ) : null}
    </div>
  );
}
