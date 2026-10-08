export async function request<T>(path:string, options:RequestInit = {}):Promise<T> {
  const response = await fetch(`/api${path}`, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(typeof error.detail === 'string' ? error.detail : `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}
