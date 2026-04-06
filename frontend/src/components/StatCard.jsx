import React from 'react';

export default function StatCard({ icon: Icon, value, label, accent = 'blue', trend }) {
  const accentColors = {
    blue: 'text-blue-400 bg-blue-500/15 border-blue-500/20',
    green: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/20',
    red: 'text-red-400 bg-red-500/15 border-red-500/20',
    amber: 'text-amber-400 bg-amber-500/15 border-amber-500/20',
  };

  const iconColors = {
    blue: 'text-blue-400',
    green: 'text-emerald-400',
    red: 'text-red-400',
    amber: 'text-amber-400',
  };

  return (
    <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 hover:border-[#475569] transition-all duration-200 hover:shadow-lg hover:shadow-black/20">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400 mb-1">{label}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {trend && (
            <p className={`text-xs mt-1 ${trend > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {trend > 0 ? '+' : ''}{trend}% from yesterday
            </p>
          )}
        </div>
        <div className={`p-2.5 rounded-lg border ${accentColors[accent]}`}>
          <Icon className={`w-5 h-5 ${iconColors[accent]}`} />
        </div>
      </div>
    </div>
  );
}
