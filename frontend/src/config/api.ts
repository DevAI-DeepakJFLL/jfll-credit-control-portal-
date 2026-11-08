/**
 * API Configuration for Jet Freight Logistics Credit Control Portal.
 * Automatically adapts between relative routes (for CloudFront / Nginx reverse proxy)
 * and absolute URLs (when VITE_API_BASE_URL is provided for direct Lambda Function URLs).
 */

export const API_BASE_URL: string = (
  (import.meta as any).env?.VITE_API_BASE_URL || ''
).replace(/\/+$/, '');

export const apiUrl = (path: string): string => {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
};
