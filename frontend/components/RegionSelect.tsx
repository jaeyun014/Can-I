"use client";

const regions = ["서울", "부산", "전주"];

type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function RegionSelect({ value, onChange }: Props) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-semibold text-ink">지역</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-12 w-full rounded-md border border-stone-300 bg-white px-4 text-base outline-none transition focus:border-mint focus:ring-4 focus:ring-mint/15"
      >
        {regions.map((region) => (
          <option key={region} value={region}>
            {region}
          </option>
        ))}
      </select>
    </label>
  );
}
