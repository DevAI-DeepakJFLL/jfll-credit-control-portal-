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

export async function parseJsonResponse<T = any>(res: Response): Promise<T> {
  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    const rawText = await res.text().catch(() => '');
    if (rawText.trim().toLowerCase().startsWith('<!doctype') || rawText.includes('<html')) {
      throw new Error(
        `Backend API service is unavailable or returned an HTML page (HTTP ${res.status}). Verify that the FastAPI backend is running on http://127.0.0.1:8001.`
      );
    }
    throw new Error(`Unexpected server response (HTTP ${res.status}): ${rawText.slice(0, 150)}`);
  }
  return res.json();
}
