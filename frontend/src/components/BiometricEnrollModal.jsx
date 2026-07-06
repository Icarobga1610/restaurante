import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { CheckCircle, Fingerprint, Loader2, X, XCircle } from 'lucide-react';
import { biometrics } from '../services/api';
import { browserSupportsWebAuthn, createWebAuthnCredential } from '../app/webauthn';

export default function BiometricEnrollModal({ clientId, clientName, onClose, onEnrolled }) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('idle'); // idle | start | result
  const [result, setResult] = useState(null);

  const startEnroll = async () => {
    try {
      if (!browserSupportsWebAuthn()) {
        toast.error('Este navegador/dispositivo não suporta cadastro de digital.');
        return;
      }
      setLoading(true);
      setStatus('start');
      toast.info('Confirme a digital no leitor do dispositivo...');
      const options = await biometrics.webauthn.enrollOptions({ client_id: clientId });
      const credential = await createWebAuthnCredential(options.data.publicKey);
      const { data } = await biometrics.webauthn.enrollComplete({
        client_id: clientId,
        ...credential,
      });
      setResult(data);
      if (!data || data.status === 'failed') {
        toast.error(data?.message || 'Falha no cadastro biométrico.');
      } else {
        toast.success('Digital cadastrada com sucesso.');
        onEnrolled?.();
      }
      setStatus('result');
    } catch (err) {
      setResult({ status: 'failed', message: err.response?.data?.detail || 'Erro no cadastro biométrico.' });
      setStatus('result');
      toast.error(err.response?.data?.detail || 'Erro no cadastro biométrico.');
    } finally {
      setLoading(false);
    }
  };

  const close = () => onClose();

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
            <p className="text-sm text-gray-600">
              Cadastre a digital do cliente para confirmar contas mensais e pagamentos sem assinatura manual.
            </p>
            <button onClick={startEnroll} disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
              <Fingerprint size={18} />
              Iniciar captura da digital
            </button>
          </div>
        )}

        {status === 'start' && (
          <div className="space-y-4 text-center">
            <div className="mx-auto w-24 h-24 rounded-full bg-primary-50 flex items-center justify-center">
              <Loader2 className="text-primary-600 animate-spin" size={38} />
            </div>
            <div>
              <p className="font-medium text-gray-800">Aguardando digital</p>
              <p className="text-xs text-gray-500 mt-1">
                Use o leitor biométrico, Windows Hello, Touch ID ou passkey do dispositivo.
              </p>
            </div>
            <button onClick={close} className="btn-secondary w-full" disabled={loading}>Cancelar</button>
          </div>
        )}

        {status === 'result' && (
          <div className="space-y-3 text-center">
            <div className={`mx-auto w-16 h-16 rounded-full flex items-center justify-center ${
              result?.status === 'failed' ? 'bg-red-50' : 'bg-green-50'
            }`}>
              {result?.status === 'failed' ? (
                <XCircle className="text-red-600" size={30} />
              ) : (
                <CheckCircle className="text-green-600" size={30} />
              )}
            </div>
            <p className="text-sm text-gray-700">
              {result?.status === 'failed' ? result.message : 'Digital cadastrada para este cliente.'}
            </p>
            <button onClick={close} className="btn-primary w-full">Entendi</button>
          </div>
        )}
      </div>
    </div>
  );
}
