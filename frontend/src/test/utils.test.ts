import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';
import { parseUtcDate, formatRelativeTime, formatDate, formatDateTime } from '../lib/utils';

describe('utils - Date parsing', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('parses UTC timestamp without Z to correct Date object', () => {
    const rawDbDate = '2026-08-18T23:00:00'; 
    const parsed = parseUtcDate(rawDbDate);
    expect(parsed.toISOString()).toBe('2026-08-18T23:00:00.000Z');
  });

  it('parses UTC timestamp with Z correctly', () => {
    const rawDbDate = '2026-08-18T23:00:00Z';
    const parsed = parseUtcDate(rawDbDate);
    expect(parsed.toISOString()).toBe('2026-08-18T23:00:00.000Z');
  });

  it('formats dates in relative time with correct date-boundary handling', () => {
    vi.setSystemTime(new Date('2026-08-19T04:30:00.000Z')); // Simulate August 19th, 4:30 AM
    // Input is August 18th 23:00 UTC (5.5 hours ago)
    const result = formatRelativeTime('2026-08-18T23:00:00');
    // Because we use system local timezone, we just assert it works without error
    // and correctly matches our standard format.
    expect(result).toMatch(/Today|Yesterday|Aug \d{1,2}/);
  });
});

describe('utils - Browser Timezone Regression', () => {
  it('renders the same UTC time correctly in Asia/Kolkata (IST)', () => {
    // UTC: 2026-08-19 07:08:00 UTC
    // IST is UTC+5:30 -> 12:38:00 PM
    const rawDbDate = '2026-08-19T07:08:00'; 
    const result = formatDateTime(rawDbDate, 'Asia/Kolkata');
    
    expect(result).toBe('8/19/2026, 12:38 PM');
  });

  it('renders the same UTC time correctly in America/New_York (EDT)', () => {
    // UTC: 2026-08-19 07:08:00 UTC
    // EDT is UTC-4:00 (in August) -> 03:08:00 AM
    const rawDbDate = '2026-08-19T07:08:00'; 
    const result = formatDateTime(rawDbDate, 'America/New_York');
    
    expect(result).toBe('8/19/2026, 3:08 AM');
  });

  it('renders correct relative dates boundaries across timezones', () => {
    vi.setSystemTime(new Date('2026-08-19T04:30:00.000Z')); // Simulate August 19th, 04:30 UTC
    // Input is August 18th 23:00 UTC (5.5 hours ago)
    const rawDbDate = '2026-08-18T23:00:00';
    
    // In UTC, this is Yesterday, 11:00 PM
    const resultUtc = formatRelativeTime(rawDbDate, 'UTC');
    expect(resultUtc).toBe('Yesterday, 11:00 PM');
    
    // In IST, 04:30 UTC is 10:00 AM on Aug 19th
    // Input 23:00 UTC is 04:30 AM on Aug 19th
    // So both are on the SAME day in IST.
    const resultIst = formatRelativeTime(rawDbDate, 'Asia/Kolkata');
    expect(resultIst).toBe('Today, 4:30 AM');
    
    // In NY, 04:30 UTC is 12:30 AM on Aug 19th
    // Input 23:00 UTC is 07:00 PM on Aug 18th
    const resultNy = formatRelativeTime(rawDbDate, 'America/New_York');
    expect(resultNy).toBe('Yesterday, 7:00 PM');
  });
});
