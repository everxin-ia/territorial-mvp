import React, { useEffect, useMemo, useState } from "react";
import { apiGet } from "../api/client";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

type Signal = {
  id: number;
  title: string;
  url: string;
  captured_at: string;
  published_at?: string;
  topics: { topic: string; score: number }[];
  territories: { territory: string; confidence: number }[];
};

type AlertEvent = {
  id: number;
  territory: string;
  prob: number;
  confidence: number;
  explanation: string;
  triggered_at: string;
  status: string;
};

export default function App() {
  const [tab, setTab] = useState<"resumen" | "senales" | "alertas">("resumen");
  const [signals, setSignals] = useState<Signal[]>([]);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    (async () => {
      try {
        const s = await apiGet<Signal[]>(`/signals?tenant_id=1&limit=100`);
        setSignals(s);
        const a = await apiGet<AlertEvent[]>(`/alerts?tenant_id=1&limit=100`);
        setAlerts(a);
      } catch (e: any) {
        setError(e?.message ?? "Error");
      }
    })();
  }, []);

  const byDay = useMemo(() => {
    const map = new Map<string, number>();
    for (const s of signals) {
      const d = new Date(s.captured_at);
      const key = d.toISOString().slice(0, 10);
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return Array.from(map.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([date, count]) => ({ date, count }));
  }, [signals]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="px-6 py-4 bg-white shadow-sm flex items-center justify-between">
        <div>
          <div className="text-xl font-semibold">MVP Inteligencia Territorial</div>
          <div className="text-sm text-slate-500">Demo end-to-end (señales → riesgo → alertas)</div>
        </div>
        <nav className="flex gap-2">
          <button className={`px-3 py-2 rounded-lg ${tab==="resumen"?"bg-slate-900 text-white":"bg-slate-200"}`} onClick={() => setTab("resumen")}>Resumen</button>
          <button className={`px-3 py-2 rounded-lg ${tab==="senales"?"bg-slate-900 text-white":"bg-slate-200"}`} onClick={() => setTab("senales")}>Señales</button>
          <button className={`px-3 py-2 rounded-lg ${tab==="alertas"?"bg-slate-900 text-white":"bg-slate-200"}`} onClick={() => setTab("alertas")}>Alertas</button>
        </nav>
      </header>

      <main className="p-6">
        {error && <div className="mb-4 p-3 rounded-lg bg-red-100 text-red-800">{error}</div>}

        {tab === "resumen" && (
          <div className="grid gap-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card title="Señales (últimas 100)" value={signals.length.toString()} />
              <Card title="Alertas (últimas 100)" value={alerts.length.toString()} />
              <Card title="Export" value="CSV" note="backend: /export/*" />
            </div>

            <div className="bg-white rounded-2xl shadow-sm p-4">
              <div className="font-semibold mb-2">Señales por día (captura)</div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={byDay}>
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="count" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="text-xs text-slate-500 mt-2">
                Nota: el riesgo se calcula en backend cada 60 min (ver scheduler).
              </div>
            </div>
          </div>
        )}

        {tab === "senales" && (
          <div className="bg-white rounded-2xl shadow-sm p-4">
            <div className="font-semibold mb-3">Explorador de señales</div>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-slate-500">
                  <tr>
                    <th className="py-2 pr-4">Título</th>
                    <th className="py-2 pr-4">Territorio</th>
                    <th className="py-2 pr-4">Tópico</th>
                    <th className="py-2 pr-4">Captura</th>
                  </tr>
                </thead>
                <tbody>
                  {signals.map((s) => (
                    <tr key={s.id} className="border-t">
                      <td className="py-2 pr-4">
                        <a className="text-blue-700 hover:underline" href={s.url} target="_blank">
                          {s.title}
                        </a>
                      </td>
                      <td className="py-2 pr-4">{s.territories?.[0]?.territory ?? "-"}</td>
                      <td className="py-2 pr-4">{s.topics?.[0]?.topic ?? "-"}</td>
                      <td className="py-2 pr-4">{new Date(s.captured_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="text-xs text-slate-500 mt-3">
              Para export: <code>/export/signals.csv?tenant_id=1</code>
            </div>
          </div>
        )}

        {tab === "alertas" && (
          <div className="bg-white rounded-2xl shadow-sm p-4">
            <div className="font-semibold mb-3">Alertas</div>
            <div className="space-y-3">
              {alerts.map((a) => (
                <div key={a.id} className="p-3 rounded-xl bg-slate-50 border">
                  <div className="flex items-center justify-between">
                    <div className="font-medium">{a.territory}</div>
                    <div className="text-xs text-slate-500">{new Date(a.triggered_at).toLocaleString()}</div>
                  </div>
                  <div className="text-sm mt-1">
                    prob={a.prob.toFixed(2)} · conf={a.confidence.toFixed(2)} · status={a.status}
                  </div>
                  <div className="text-xs text-slate-600 mt-2 whitespace-pre-wrap">{a.explanation}</div>
                </div>
              ))}
              {alerts.length === 0 && <div className="text-slate-500 text-sm">No hay alertas todavía.</div>}
            </div>
            <div className="text-xs text-slate-500 mt-3">
              Configura webhook en <code>backend/.env</code> (ALERT_WEBHOOK_URL).
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function Card({ title, value, note }: { title: string; value: string; note?: string }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-4">
      <div className="text-sm text-slate-500">{title}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
      {note && <div className="text-xs text-slate-500 mt-2">{note}</div>}
    </div>
  );
}
