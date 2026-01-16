export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`)
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json() as Promise<T>
}
