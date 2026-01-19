'use client';

interface SwitchProps {
  checked: boolean;
  label: string;
  onChange?: (checked: boolean) => void;
}

export const Switch = ({ checked, label, onChange }: SwitchProps) => {
  const handleClick = () => {
    if (onChange) {
      onChange(!checked);
    }
  };
  
  return (
    <div 
      onClick={handleClick}
      className="flex items-center justify-between group cursor-pointer touch-manipulation py-1"
    >
      <span className="text-[10px] md:text-[11px] text-slate-400 font-medium group-hover:text-slate-200 transition-colors flex-1 pr-2">{label}</span>
      <div className={`w-9 md:w-10 h-5 md:h-6 rounded-full p-0.5 transition-colors shrink-0 ${checked ? 'bg-blue-600' : 'bg-slate-700'}`}>
        <div className={`w-4 h-4 bg-white rounded-full transition-transform ${checked ? 'translate-x-4 md:translate-x-4' : 'translate-x-0'}`} />
      </div>
    </div>
  );
};
