'use client';

type Year = 1 | 5 | 10;

interface TimeSliderProps {
  selectedYear: Year;
  onYearChange: (year: Year) => void;
}

const OPTIONS: { year: Year; label: string }[] = [
  { year: 1,  label: '1 Year'  },
  { year: 5,  label: '5 Years' },
  { year: 10, label: '10 Years' },
];

export default function TimeSlider({ selectedYear, onYearChange }: TimeSliderProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="text-xs text-slate-400 font-medium uppercase tracking-widest">
        Projecting: {selectedYear} year{selectedYear !== 1 ? 's' : ''} out
      </div>
      <div className="flex gap-2">
        {OPTIONS.map(({ year, label }) => (
          <button
            key={year}
            onClick={() => onYearChange(year)}
            className={`
              flex-1 py-2 px-3 rounded-lg text-sm font-semibold border transition-all duration-150
              ${selectedYear === year
                ? 'bg-amber-500 border-amber-400 text-slate-900'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:border-amber-500/50 hover:text-amber-400'}
            `}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
