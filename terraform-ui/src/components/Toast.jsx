// Add to your project: components/Toast.jsx
import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Info } from 'lucide-react';

function Toast({ message, type = 'success', onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const icons = {
    success: <CheckCircle className="w-5 h-5" />,
    error: <XCircle className="w-5 h-5" />,
    info: <Info className="w-5 h-5" />
  };

  const colors = {
    success: 'from-green-500 to-emerald-600',
    error: 'from-red-500 to-red-600',
    info: 'from-blue-500 to-blue-600'
  };

  return (
    <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-top duration-300">
      <div className={`bg-gradient-to-r ${colors[type]} text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 max-w-sm`}>
        {icons[type]}
        <span className="font-medium">{message}</span>
        <button onClick={onClose} className="ml-2 hover:bg-white/20 rounded-full p-1">
          ×
        </button>
      </div>
    </div>
  );
}

export default Toast;
