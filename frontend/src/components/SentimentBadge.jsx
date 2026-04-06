import React from 'react';

const config = {
  positive: {
    label: 'Positive',
    bg: 'bg-emerald-500/15',
    text: 'text-emerald-400',
    border: 'border-emerald-500/30',
  },
  negative: {
    label: 'Negative',
    bg: 'bg-red-500/15',
    text: 'text-red-400',
    border: 'border-red-500/30',
  },
  neutral: {
    label: 'Neutral',
    bg: 'bg-amber-500/15',
    text: 'text-amber-400',
    border: 'border-amber-500/30',
  },
};

export default function SentimentBadge({ sentiment }) {
  const key = (sentiment || 'neutral').toLowerCase();
  const c = config[key] || config.neutral;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${c.bg} ${c.text} ${c.border}`}
    >
      {c.label}
    </span>
  );
}
