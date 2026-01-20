import React, { useEffect, useMemo, useState } from "react";
import { apiGet } from "../api/client";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import MapView from "../components/Map";
import Filters from "../components/Filters";
import AlertDetail from "../components/AlertDetail";
import RulesManager from "../components/RulesManager";

type Signal = {
  id: number;
  title: string;
  url: string;
  captured_at: string;
  published_at?: string;
  sentiment_score: number;
  sentiment_label: string;
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
  const [tab, setTab] = useState<"resumen" | "mapa" | "senales" | "alertas" | "config">("resumen");
  const [signals, setSignals] = useState<Signal[]>([]);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [error, setError] = useState<string>("");
  const [filters, setFilters] = useState({ territory: "", topic: "", days: "" });
  const [selectedAlert, setSelectedAlert] = useState<number | null>(null);

  useEffect(() => {
    loadData();
  }, [filters]);

  const loadData = async () => {
    try {
      const params = new URLSearchParams({ tenant_id: "1", limit: "100" });
      if (filters.territory) params.append("territory", filters.territory);
      if (filters.topic) params.append("topic", filters.topic);
      if (filters.days) params.append("days", filters.days);

      const s = await apiGet<Signal[]>(`/signals?${params.toString()}`);
      setSignals(s);
      const a = await apiGet<AlertEvent[]>(`/alerts?tenant_id=1&limit=100`);
      setAlerts(a);
    } catch (e: any) {
      setError(e?.message ?? "Error");
    }
  };

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

  const sentimentDistribution = useMemo(() => {
    const counts = { positive: 0, neutral: 0, negative: 0 };
    signals.forEach((s) => {
      if (s.sentiment_label === "positive") counts.positive++;
      else if (s.sentiment_label === "negative") counts.negative++;
      else counts.neutral++;
    });
    return [
      { name: "Positivo", value: counts.positive },
      { name: "Neutral", value: counts.neutral },
      { name: "Negativo", value: counts.negative },
    ];
  }, [signals]);

  const topTopics = useMemo(() => {
    const topicCounts = new Map<string, number>();
    signals.forEach((s) => {
      s.topics.forEach((t) => {
        topicCounts.set(t.topic, (topicCounts.get(t.topic) ?? 0) + 1);
      });
    });
    return Array.from(topicCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([topic, count]) => ({ topic, count }));
  }, [signals]);

  const getSentimentBadge = (label: string) => {
    const colors = {
      positive: "bg-green-100 text-green-800",
      negative: "bg-red-100 text-red-800",
      neutral: "bg-slate-100 text-slate-800",
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${colors[label as keyof typeof colors] || colors.neutral}`}>
        {label}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="px-6 py-4 bg-white shadow-sm">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-2xl font-bold">MVP Inteligencia Territorial</div>
              <div className="text-sm text-slate-500">
                Plataforma de detección temprana de conflictos socio-territoriales
              </div>
            </div>
            <div className="text-sm text-slate-500">v2.0.0 Enhanced</div>
          </div>
          <nav className="flex gap-2">
            <TabButton
              label="Resumen"
              active={tab === "resumen"}
              onClick={() => setTab("resumen")}
            />
            <TabButton label="Mapa" active={tab === "mapa"} onClick={() => setTab("mapa")} />
            <TabButton
              label="Señales"
              active={tab === "senales"}
              onClick={() => setTab("senales")}
            />
            <TabButton
              label="Alertas"
              active={tab === "alertas"}
              onClick={() => setTab("alertas")}
            />
            <TabButton
              label="Configuración"
              active={tab === "config"}
              onClick={() => setTab("config")}
            />
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        {error && <div className="mb-4 p-3 rounded-lg bg-red-100 text-red-800">{error}</div>}

        {tab === "resumen" && (
          <div className="grid gap-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card title="Señales Totales" value={signals.length.toString()} />
              <Card
                title="Alertas Activas"
                value={alerts.filter((a) => a.status === "new").length.toString()}
                color="red"
              />
              <Card
                title="Territoriosaumentados"
                value={new Set(signals.flatMap((s) => s.territories.map((t) => t.territory))).size.toString()}
              />
              <Card
                title="Promedio Sentiment"
                value={
                  signals.length > 0
                    ? (
                        signals.reduce((sum, s) => sum + s.sentiment_score, 0) / signals.length
                      ).toFixed(2)
                    : "0"
                }
                color={
                  signals.length > 0 &&
                  signals.reduce((sum, s) => sum + s.sentiment_score, 0) / signals.length < -0.2
                    ? "red"
                    : "green"
                }
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ChartCard title="Señales por Día">
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={byDay}>
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="count" stroke="#1e293b" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Distribución de Sentiment">
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={sentimentDistribution}>
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#1e293b" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>

            <ChartCard title="Top 5 Tópicos">
              <div className="space-y-2">
                {topTopics.map(({ topic, count }) => (
                  <div key={topic} className="flex items-center justify-between">
                    <span className="text-sm font-medium capitalize">{topic}</span>
                    <div className="flex items-center gap-2">
                      <div className="h-2 bg-slate-200 rounded-full w-32">
                        <div
                          className="h-2 bg-slate-900 rounded-full"
                          style={{
                            width: `${(count / Math.max(...topTopics.map((t) => t.count))) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="text-sm text-slate-600 w-8 text-right">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </ChartCard>
          </div>
        )}

        {tab === "mapa" && (
          <div>
            <div className="mb-4">
              <h2 className="text-xl font-semibold mb-2">Mapa de Riesgo Territorial</h2>
              <p className="text-sm text-slate-600">
                Los círculos representan el nivel de riesgo. Haz clic en los marcadores para más detalles.
              </p>
            </div>
            <MapView />
          </div>
        )}

        {tab === "senales" && (
          <div>
            <Filters territory={filters.territory} topic={filters.topic} days={filters.days} onFilterChange={setFilters} />
            <div className="bg-white rounded-2xl shadow-sm p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="font-semibold">Explorador de Señales</div>
                <div className="text-sm text-slate-500">{signals.length} resultados</div>
              </div>
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead className="text-left text-slate-500 border-b">
                    <tr>
                      <th className="py-2 pr-4">Título</th>
                      <th className="py-2 pr-4">Territorio</th>
                      <th className="py-2 pr-4">Tópico</th>
                      <th className="py-2 pr-4">Sentiment</th>
                      <th className="py-2 pr-4">Captura</th>
                    </tr>
                  </thead>
                  <tbody>
                    {signals.map((s) => (
                      <tr key={s.id} className="border-t hover:bg-slate-50">
                        <td className="py-3 pr-4">
                          <a
                            className="text-blue-700 hover:underline"
                            href={s.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {s.title}
                          </a>
                        </td>
                        <td className="py-3 pr-4">
                          {s.territories?.[0]?.territory ?? "-"}
                        </td>
                        <td className="py-3 pr-4 capitalize">
                          {s.topics?.[0]?.topic ?? "-"}
                        </td>
                        <td className="py-3 pr-4">
                          {getSentimentBadge(s.sentiment_label)}
                        </td>
                        <td className="py-3 pr-4 text-slate-500">
                          {new Date(s.captured_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {tab === "alertas" && (
          <div className="bg-white rounded-2xl shadow-sm p-4">
            <div className="font-semibold mb-4">Alertas</div>
            <div className="space-y-3">
              {alerts.map((a) => (
                <div
                  key={a.id}
                  className={`p-4 rounded-xl border-l-4 ${
                    a.status === "new"
                      ? "border-red-500 bg-red-50"
                      : a.status === "acked"
                      ? "border-yellow-500 bg-yellow-50"
                      : "border-green-500 bg-green-50"
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="font-medium text-lg">{a.territory}</div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          a.status === "new"
                            ? "bg-red-100 text-red-800"
                            : a.status === "acked"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-green-100 text-green-800"
                        }`}
                      >
                        {a.status}
                      </span>
                      <span className="text-xs text-slate-500">
                        {new Date(a.triggered_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <div className="text-sm mb-2">
                    <span className="font-medium">Probabilidad:</span>{" "}
                    <span className="font-bold text-red-600">{(a.prob * 100).toFixed(1)}%</span>
                    {" · "}
                    <span className="font-medium">Confianza:</span> {(a.confidence * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-slate-700 whitespace-pre-wrap mb-3">
                    {a.explanation}
                  </div>
                  <button
                    onClick={() => setSelectedAlert(a.id)}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    Ver comentarios →
                  </button>
                </div>
              ))}
              {alerts.length === 0 && (
                <div className="text-slate-500 text-sm text-center py-8">
                  No hay alertas todavía.
                </div>
              )}
            </div>
          </div>
        )}

        {tab === "config" && (
          <div>
            <RulesManager />
          </div>
        )}

        {selectedAlert && (
          <AlertDetail alertId={selectedAlert} onClose={() => setSelectedAlert(null)} />
        )}
      </main>
    </div>
  );
}

function TabButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={`px-4 py-2 rounded-lg font-medium transition-colors ${
        active ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
      }`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

function Card({
  title,
  value,
  color = "slate",
}: {
  title: string;
  value: string;
  color?: string;
}) {
  const colorClasses = {
    slate: "text-slate-900",
    red: "text-red-600",
    green: "text-green-600",
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm p-4">
      <div className="text-sm text-slate-500 mb-1">{title}</div>
      <div className={`text-3xl font-bold ${colorClasses[color as keyof typeof colorClasses] || colorClasses.slate}`}>
        {value}
      </div>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-4">
      <div className="font-semibold mb-4">{title}</div>
      {children}
    </div>
  );
}
