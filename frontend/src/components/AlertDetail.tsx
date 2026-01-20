import React, { useState, useEffect } from "react";
import { apiGet } from "../api/client";

type Comment = {
  id: number;
  user_name: string;
  comment: string;
  created_at: string;
};

type AlertDetailProps = {
  alertId: number;
  onClose: () => void;
};

export default function AlertDetail({ alertId, onClose }: AlertDetailProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [userName, setUserName] = useState("Usuario");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadComments();
  }, [alertId]);

  const loadComments = async () => {
    try {
      const data = await apiGet<Comment[]>(`/alert-rules/${alertId}/comments`);
      setComments(data);
    } catch (e) {
      console.error("Error loading comments:", e);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/alert-rules/${alertId}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_name: userName, comment: newComment }),
      });

      if (!response.ok) throw new Error("Failed to post comment");

      setNewComment("");
      await loadComments();
    } catch (e) {
      alert("Error al publicar comentario");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] flex flex-col">
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h2 className="text-xl font-semibold">Comentarios de la Alerta #{alertId}</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {comments.length === 0 ? (
            <div className="text-center text-slate-500 py-8">
              No hay comentarios todavía. Sé el primero en comentar.
            </div>
          ) : (
            comments.map((c) => (
              <div key={c.id} className="bg-slate-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-slate-900">{c.user_name}</span>
                  <span className="text-xs text-slate-500">
                    {new Date(c.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="text-slate-700">{c.comment}</div>
              </div>
            ))
          )}
        </div>

        <div className="px-6 py-4 border-t">
          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <input
                type="text"
                placeholder="Tu nombre"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
              />
            </div>
            <div>
              <textarea
                placeholder="Escribe un comentario..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 resize-none"
                rows={3}
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300"
              >
                Cerrar
              </button>
              <button
                type="submit"
                disabled={loading || !newComment.trim()}
                className="px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-700 disabled:opacity-50"
              >
                {loading ? "Publicando..." : "Publicar"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
