"use client";

const regionGroups: Record<string, string[]> = {
  "서울특별시": ["강남구", "마포구"],
  "부산광역시": ["해운대구"],
  "전주시": ["완산구"],
  "제주특별자치도": ["제주시"]
};

function splitRegion(value: string) {
  for (const [city, districts] of Object.entries(regionGroups)) {
    if (value.startsWith(city)) {
      const district = districts.find((item) => value.endsWith(item)) ?? districts[0];
      return { city, district };
    }
  }

  return { city: "서울특별시", district: "강남구" };
}

function joinRegion(city: string, district: string) {
  return `${city} ${district}`;
}

type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function RegionSelect({ value, onChange }: Props) {
  const { city, district } = splitRegion(value);
  const districts = regionGroups[city];

  function handleCityChange(nextCity: string) {
    onChange(joinRegion(nextCity, regionGroups[nextCity][0]));
  }

  function handleDistrictChange(nextDistrict: string) {
    onChange(joinRegion(city, nextDistrict));
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <label className="block">
        <span className="mb-2 block text-sm font-semibold text-ink">시/도</span>
        <select
          value={city}
          onChange={(event) => handleCityChange(event.target.value)}
          className="h-12 w-full rounded-md border border-stone-300 bg-white px-4 text-base outline-none transition focus:border-mint focus:ring-4 focus:ring-mint/15"
        >
          {Object.keys(regionGroups).map((regionCity) => (
            <option key={regionCity} value={regionCity}>
              {regionCity}
            </option>
          ))}
        </select>
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-semibold text-ink">구/군</span>
        <select
          value={district}
          onChange={(event) => handleDistrictChange(event.target.value)}
          className="h-12 w-full rounded-md border border-stone-300 bg-white px-4 text-base outline-none transition focus:border-mint focus:ring-4 focus:ring-mint/15"
        >
          {districts.map((regionDistrict) => (
            <option key={regionDistrict} value={regionDistrict}>
              {regionDistrict}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
