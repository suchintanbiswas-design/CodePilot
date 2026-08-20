import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function parseUtcDate(dateInput: string | Date): Date {
  if (dateInput instanceof Date) return dateInput;
  let dateStr = dateInput;
  // FastAPI serializes naive UTC datetimes as "YYYY-MM-DDTHH:MM:SS"
  // JavaScript Date parses these as local time if they lack 'Z'.
  if (!dateStr.endsWith('Z') && !dateStr.match(/[+-]\d{2}:\d{2}$/)) {
    dateStr += 'Z';
  }
  return new Date(dateStr);
}

export function formatDate(date: string | Date, timeZone?: string): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    timeZone,
  }).format(parseUtcDate(date));
}

export function formatDateTime(date: string | Date, timeZone?: string): string {
  return parseUtcDate(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    timeZone,
  });
}

export function formatRelativeTime(date: string | Date, timeZone?: string): string {
  const parsedDate = parseUtcDate(date);
  const now = new Date();

  const timeString = parsedDate.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    timeZone,
  });

  // Calculate local dates using the provided timezone if available
  const formatter = new Intl.DateTimeFormat('en-US', { 
    timeZone,
    month: 'short',
    day: 'numeric'
  });
  
  const parsedLocalString = formatter.format(parsedDate);
  const nowLocalString = formatter.format(now);

  // We have to parse yesterday's local string accurately based on the timezone
  const yesterday = new Date(now.getTime() - (24 * 60 * 60 * 1000));
  const yesterdayLocalString = formatter.format(yesterday);

  if (parsedLocalString === nowLocalString) {
    return `Today, ${timeString}`;
  } else if (parsedLocalString === yesterdayLocalString) {
    return `Yesterday, ${timeString}`;
  } else {
    return `${parsedLocalString}, ${timeString}`;
  }
}

export function formatScore(score: number): string {
  return `${Math.round(score)}%`;
}

export function truncateText(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + '...';
}
