'use client';
import { useState } from 'react';

export const BlackHorseLogo = ({ className }: { className?: string }) => {
  const [hasError, setHasError] = useState(false);
  return (
    <div className={`${className} flex items-center justify-center overflow-hidden`}>
      {!hasError ? (
        <img 
          src="/logo.png" 
          alt="黑马量化" 
          className="w-full h-full object-contain"
          onError={() => setHasError(true)}
        />
      ) : (
        <span className="text-blue-500 font-black text-xl italic leading-none">H</span>
      )}
    </div>
  );
};
