import React, { useState, useEffect } from "react";
import { apiGet } from "../api/client";

type AlertRule = {
  id: number;
  name: string;
  territory_filter: string;
  topic_filter: string;
  min_prob: number;
  min_confidence: number;
  enabled: boolean;
};

export default function RulesManager() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      const data = await apiGet<AlertRule[]>("/alert-rules?tenant_id=1");
      setRules(data);
    } catch (e) {
      console.error("Error loading rules:", e);
    }
  };

  const handleSave = async (rule: Partial<AlertRule>) => {
    try {
      const url = editingRule
        ? `/api/alert-rules/${editingRule.id}`
        : `/api/alert-rules?tenant_id=1`;
      const method = editingRule ? "PUT" : "POST";

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(rule),
      });

      if (!response.ok) throw new Error("Failed to save rule");

      await loadRules();
      setEditingRule(null);
      setShowForm(false);
    } catch (e) {
      alert("Error al guardar regla");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("¿Eliminar esta regla?")) return;

    try {
      const response = await fetch(`/api/alert-rules/${id}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Failed to delete rule");
      await loadRules();
    } catch (e) {
      alert("Error al eliminar regla");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Reglas de Alerta</h2>
        <button
          onClick={() => {
            setEditingRule(null);
            setShowForm(true);
          }}
          className="px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-700"
        >
          + Nueva Regla
        </button>
      </div>

      {showForm && <RuleForm rule={editingRule} onSave={handleSave} onCancel={() => setShowForm(false)} />}

      <div className="space-y-3">
        {rules.map((rule) => (
          <div key={rule.id} className="bg-white rounded-xl shadow-sm p-4 border">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-semibold text-lg">{rule.name}</h3>
                  {!rule.enabled && (
                    <span className="px-2 py-1 bg-slate-200 text-slate-600 text-xs rounded">
                      Deshabilitada
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm text-slate-600">
                  <div>
                    <span className="font-medium">Territorio:</span>{" "}
                    {rule.territory_filter || "Todos"}
                  </div>
                  <div>
                    <span className="font-medium">Tópico:</span> {rule.topic_filter || "Todos"}
                  </div>
                  <div>
                    <span className="font-medium">Prob. mín:</span> {(rule.min_prob * 100).toFixed(0)}%
                  </div>
                  <div>
                    <span className="font-medium">Conf. mín:</span>{" "}
                    {(rule.min_confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setEditingRule(rule);
                    setShowForm(true);
                  }}
                  className="px-3 py-1 bg-slate-100 text-slate-700 rounded hover:bg-slate-200 text-sm"
                >
                  Editar
                </button>
                <button
                  onClick={() => handleDelete(rule.id)}
                  className="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm"
                >
                  Eliminar
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RuleForm({
  rule,
  onSave,
  onCancel,
}: {
  rule: AlertRule | null;
  onSave: (rule: Partial<AlertRule>) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState({
    name: rule?.name || "",
    territory_filter: rule?.territory_filter || "",
    topic_filter: rule?.topic_filter || "",
    min_prob: rule?.min_prob || 0.6,
    min_confidence: rule?.min_confidence || 0.4,
    enabled: rule?.enabled ?? true,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-slate-50 rounded-xl p-4 border-2 border-slate-900">
      <h3 className="font-semibold mb-4">{rule ? "Editar Regla" : "Nueva Regla"}</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium mb-1">Nombre</label>
          <input
            type="text"
            required
            className="w-full px-3 py-2 border border-slate-300 rounded-lg"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Filtro Territorio</label>
          <input
            type="text"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg"
            placeholder="Opcional"
            value={formData.territory_filter}
            onChange={(e) => setFormData({ ...formData, territory_filter: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Filtro Tópico</label>
          <input
            type="text"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg"
            placeholder="Opcional"
            value={formData.topic_filter}
            onChange={(e) => setFormData({ ...formData, topic_filter: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">
            Probabilidad Mínima: {(formData.min_prob * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            className="w-full"
            value={formData.min_prob}
            onChange={(e) => setFormData({ ...formData, min_prob: parseFloat(e.target.value) })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">
            Confianza Mínima: {(formData.min_confidence * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            className="w-full"
            value={formData.min_confidence}
            onChange={(e) =>
              setFormData({ ...formData, min_confidence: parseFloat(e.target.value) })
            }
          />
        </div>
        <div className="md:col-span-2">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.enabled}
              onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
            />
            <span className="text-sm font-medium">Habilitada</span>
          </label>
        </div>
      </div>
      <div className="flex justify-end gap-2 mt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300"
        >
          Cancelar
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-700"
        >
          Guardar
        </button>
      </div>
    </form>
  );
}
