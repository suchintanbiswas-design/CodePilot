import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

interface ScoreGaugeProps {
  value: number;
  label: string;
  size?: 'sm' | 'md' | 'lg';
}

export function ScoreGauge({ value, label, size = 'md' }: ScoreGaugeProps) {
  const getColor = (val: number) => {
    if (val >= 90) return '#22c55e'; // green-500
    if (val >= 70) return '#eab308'; // yellow-500
    return '#ef4444'; // red-500
  };

  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-24 h-24',
    lg: 'w-32 h-32',
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-2">
      <div className={sizeClasses[size]}>
        <CircularProgressbar
          value={value}
          text={`${value}`}
          styles={buildStyles({
            textSize: '24px',
            pathColor: getColor(value),
            textColor: 'var(--color-text-primary)',
            trailColor: 'var(--color-border)',
          })}
        />
      </div>
      <span className="text-sm font-medium text-[var(--color-text-secondary)]">{label}</span>
    </div>
  );
}
