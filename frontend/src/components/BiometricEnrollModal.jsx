import React, { useEffect, useRef, useState } from 'react';
import { toast } from 'react-toastify';
import { X, Fingerprint } from 'lucide-react';
import { biometrics } from '../services/api';
import { useAuth } from '../hooks/useAuth';

export default function BiometricEnrollModal({ clientId, clientName, onClose, onEnrolled }) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('idle'); // idle | start | result
  const [result, setResult] = useState(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const { token } = useAuth();

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  const startEnroll = async () => {
    try {
      setLoading(true);
      setStatus('start');
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      toast.info('Posicione o dedo no leitor e aguarde a captura...');
      const { data } = await biometrics.enroll({ client_id: clientId });
      setResult(data);
      if (!data || data.status === 'failed') {
        toast.error(data?.message || 'Falha no cadastro biométrico.');
      } else {
        toast.success('Digital cadastrada com sucesso.');
        onEnrolled?.();
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro no cadastro biométrico.');
    } finally {
      setLoading(false);
    }
  };

  const close = () => {
    if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={close}>
      <div className="bg-white rounded-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary-50 rounded-xl"><Fingerprint size={20} className="text-primary-600"/></div>
            <div>
              <h3 className="font-semibold text-gray-800">Cadastro de Digital</h3>
              <p className="text-xs text-gray-500">{clientName}</p>
            </div>
          </div>
          <button onClick={close} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500"><X size={18}/></button>
        </div>

        {status === 'idle' && (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">Cliente de conta: é necessário cadastrar a digital no ato.</p>
            <button onClick={startEnroll} disabled={loading} className="btn-primary w-full">Iniciar captura</button>
          </div>
        )}

        {status === 'start' && (
          <div className="space-y-3">
            <video ref={videoRef} autoPlay playsInline muted className="w-full rounded-lg bg-black" />
            <p className="text-xs text-gray-500">Aguardando leitor/digital...</p>
            <button onClick={close} className="btn-secondary w-full">Cancelar</button>
          </div>
        )}

        {status === 'result' && (
          <div className="space-y-3">
            <p className="text-sm text-gray-700">{result ? (result.ok ? 'Digital cadastrada.' : 'Falha ao cadastrar digital.') : 'Finalizado.'}</p>
            <button onClick={close} className="btn-primary w-full">Entendi</button>
          </div>
        )}
      </div>
    </div>
  );
}
