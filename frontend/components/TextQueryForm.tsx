"use client";

type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function TextQueryForm({ value, onChange }: Props) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-semibold text-ink">물건 이름</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="예: 알루미늄 포일, 종이컵, 보조배터리"
        className="h-12 w-full rounded-md border border-stone-300 bg-white px-4 text-base outline-none transition placeholder:text-stone-400 focus:border-mint focus:ring-4 focus:ring-mint/15"
      />
    </label>
  );
}
