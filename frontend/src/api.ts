const API_URL = import.meta.env.VITE_API_URL as string;
const API_KEY = import.meta.env.VITE_API_KEY as string;

export interface QueryRequest {
  query: string;
  thread_id?: string;
}

export interface QueryResponse {
  answer: string;
  thread_id: string;
  sources?: string[];
}

export async function runQuery(request: QueryRequest): Promise<QueryResponse> {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(API_KEY ? { "X-Api-Key": API_KEY } : {}),
    },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`Request failed (${res.status}): ${text}`);
  }

  return res.json() as Promise<QueryResponse>;
}
