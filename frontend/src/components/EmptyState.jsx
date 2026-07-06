import React from 'react';
import { Inbox, AlertCircle } from 'lucide-react';

export default function EmptyState({
  title = 'Nenhum registro encontrado',
  description = 'Cadastre ou ajuste os filtros para ver resultados.',
  action,
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="bg-gray-100 text-gray-400 rounded-full p-3 mb-3">
        <Inbox size={28} />
      </div>
      <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
      <p className="text-xs text-gray-500 mt-1 max-w-sm">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function ErrorState({ message = 'Erro ao carregar', onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="bg-red-50 text-red-500 rounded-full p-3 mb-3">
        <AlertCircle size={28} />
      </div>
      <h3 className="text-sm font-semibold text-gray-700">{message}</h3>
      {onRetry ? (
        <button
          onClick={onRetry}
          className="mt-3 text-xs px-3 py-2 bg-gray-900 text-white rounded-md"
        >
          Tentar novamente
        </button>
      ) : null}
    </div>
  );
}
