import React from "react";

type FiltersProps = {
  territory: string;
  topic: string;
  days: string;
  onFilterChange: (filters: { territory: string; topic: string; days: string }) => void;
};

export default function Filters({ territory, topic, days, onFilterChange }: FiltersProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
      <div className="font-semibold mb-3">Filtros</div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label className="block text-sm text-slate-600 mb-1">Territorio</label>
          <input
            type="text"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
            placeholder="Ej: Santiago"
            value={territory}
            onChange={(e) => onFilterChange({ territory: e.target.value, topic, days })}
          />
        </div>
        <div>
          <label className="block text-sm text-slate-600 mb-1">Tópico</label>
          <select
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
            value={topic}
            onChange={(e) => onFilterChange({ territory, topic: e.target.value, days })}
          >
            <option value="">Todos</option>
            <option value="socioambiental">Socioambiental</option>
            <option value="regulatorio">Regulatorio</option>
            <option value="laboral">Laboral</option>
            <option value="seguridad">Seguridad</option>
            <option value="reputacional">Reputacional</option>
            <option value="infraestructura">Infraestructura</option>
            <option value="politico-administrativo">Político-Administrativo</option>
          </select>
        </div>
        <div>
          <label className="block text-sm text-slate-600 mb-1">Período</label>
          <select
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
            value={days}
            onChange={(e) => onFilterChange({ territory, topic, days: e.target.value })}
          >
            <option value="">Todos</option>
            <option value="7">Últimos 7 días</option>
            <option value="14">Últimos 14 días</option>
            <option value="30">Últimos 30 días</option>
          </select>
        </div>
      </div>
    </div>
  );
}
