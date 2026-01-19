'use client';

interface FormFieldProps {
  label: string;
  description?: string;
  children: React.ReactNode;
  risk?: boolean;
}

export const FormField = ({ label, description, children, risk }: FormFieldProps) => (
  <div className="space-y-1 md:space-y-1.5">
    <div className="flex justify-between items-center gap-2">
      <label className="text-[9px] md:text-[10px] font-bold text-slate-500 uppercase tracking-tighter">{label}</label>
      {risk && <span className="text-[8px] md:text-[9px] text-rose-500 font-bold px-1 rounded border border-rose-500/30 shrink-0">高风险</span>}
    </div>
    {children}
    {description && <p className="text-[8px] md:text-[9px] text-slate-600 italic leading-tight">{description}</p>}
  </div>
);
