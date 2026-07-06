import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { monthlyAccounts as maApi } from '../services/api';
import { toast } from 'react-toastify';
import { PenTool, Trash2, CheckCircle, ArrowLeft, Shield, User, DollarSign, Calendar, FileText } from 'lucide-react';

export default function SignaturePad() {
  const navigate = useNavigate();
  const location = useLocation();
  const accountData = location.state?.account;
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);
  const [loading, setLoading] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(accountData || null);
  const [signatureBase64, setSignatureBase64] = useState('');

  useEffect(() => {
    if (!accountData) {
      // Load accounts that need signatures
      maApi.list({ status: 'closed' }).then((res) => {
        setAccounts(res.data.filter((a) => !a.signature_id));
      }).catch(() => {});
    }
  }, []);

  useEffect(() => {
    if (canvasRef.current) {
      const canvas = canvasRef.current;
      canvas.width = canvas.offsetWidth * 2;
      canvas.height = canvas.offsetHeight * 2;
      canvas.style.width = canvas.offsetWidth + 'px';
      canvas.style.height = canvas.offsetHeight + 'px';
      const ctx = canvas.getContext('2d');
      ctx.scale(2, 2);
      ctx.strokeStyle = '#1f2937';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
    }
  }, [selectedAccount]);

  const getPos = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    return {
      x: (clientX - rect.left) / (rect.width / canvas.width) / 2,
      y: (clientY - rect.top) / (rect.height / canvas.height) / 2,
    };
  };

  const startDrawing = useCallback((e) => {
    e.preventDefault();
    const pos = getPos(e);
    const ctx = canvasRef.current.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
    setIsDrawing(true);
    setHasSignature(true);
  }, []);

  const draw = useCallback((e) => {
    e.preventDefault();
    if (!isDrawing) return;
    const pos = getPos(e);
    const ctx = canvasRef.current.getContext('2d');
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
  }, [isDrawing]);

  const stopDrawing = useCallback(() => {
    setIsDrawing(false);
  }, []);

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasSignature(false);
    setSignatureBase64('');
  };

  const saveSignature = async () => {
    if (!selectedAccount) {
      toast.warning('Selecione uma conta mensal');
      return;
    }
    if (!hasSignature) {
      toast.warning('Desenhe sua assinatura');
      return;
    }

    const canvas = canvasRef.current;
    const base64 = canvas.toDataURL('image/png');
    setSignatureBase64(base64);

    setLoading(true);
    try {
      await maApi.sign(selectedAccount.id, {
        monthly_account_id: selectedAccount.id,
        client_id: selectedAccount.client_id,
        signature_data: base64,
        signed_value: selectedAccount.total,
        device_info: navigator.userAgent,
      });
      toast.success('Assinatura salva com sucesso!');
      clearCanvas();
      setSelectedAccount(null);
      navigate('/monthly-accounts');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao salvar assinatura');
    } finally {
      setLoading(false);
    }
  };

  const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

  return (
    <div className="max-w-3xl mx-auto animate-fade-in">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/monthly-accounts')} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft size={20} className="text-gray-600" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Assinatura Digital</h1>
          <p className="text-gray-500 text-sm mt-1">
            Assinatura eletrônica simples para confirmação de consumo mensal
          </p>
        </div>
      </div>

      {/* Account selection */}
      {!accountData && !selectedAccount && (
        <div className="card mb-6">
          <h2 className="font-semibold text-gray-700 mb-3">Selecione a conta para assinar</h2>
          <div className="space-y-2">
            {accounts.map((acc) => (
              <button
                key={acc.id}
                onClick={() => setSelectedAccount(acc)}
                className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-all"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-medium text-gray-800">{acc.client_name}</p>
                    <p className="text-sm text-gray-500">{months[acc.month - 1]} {acc.year} - R$ {acc.total.toFixed(2)}</p>
                  </div>
                  <PenTool size={18} className="text-primary-500" />
                </div>
              </button>
            ))}
            {accounts.length === 0 && (
              <p className="text-gray-400 text-sm">Nenhuma conta pendente de assinatura</p>
            )}
          </div>
        </div>
      )}

      {selectedAccount && (
        <>
          {/* Account info */}
          <div className="card mb-6 bg-primary-50 border-primary-100">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary-100 rounded-xl">
                <FileText size={24} className="text-primary-600" />
              </div>
              <div>
                <h2 className="font-semibold text-gray-800">{selectedAccount.client_name}</h2>
                <p className="text-sm text-gray-500">
                  {months[selectedAccount.month - 1]} {selectedAccount.year}
                </p>
              </div>
              <div className="ml-auto text-right">
                <p className="text-2xl font-bold text-gray-800">R$ {selectedAccount.total.toFixed(2)}</p>
                <p className="text-xs text-gray-500">Valor a confirmar</p>
              </div>
            </div>
          </div>

          {/* Canvas */}
          <div className="card mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-700 flex items-center gap-2">
                <PenTool size={18} />
                Assine abaixo
              </h2>
              <button
                onClick={clearCanvas}
                className="btn-secondary flex items-center gap-1 text-sm py-1.5 px-3"
                disabled={!hasSignature}
              >
                <Trash2 size={14} />
                Limpar
              </button>
            </div>

            <div className="bg-white rounded-xl border-2 border-dashed border-gray-300 hover:border-primary-400 transition-colors">
              <canvas
                ref={canvasRef}
                className="w-full h-48 cursor-crosshair touch-none"
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
                onTouchStart={startDrawing}
                onTouchMove={draw}
                onTouchEnd={stopDrawing}
              />
            </div>

            <div className="mt-3 flex items-center gap-2 text-xs text-gray-400">
              <Shield size={12} />
              <span>
                Desenhe sua assinatura usando mouse, touch ou caneta.
                {hasSignature && ' Assinatura registrada!'}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={saveSignature}
              disabled={loading || !hasSignature}
              className="btn-primary flex items-center gap-2 flex-1 justify-center py-3"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <CheckCircle size={20} />
              )}
              Confirmar Assinatura
            </button>
            <button
              onClick={() => { setSelectedAccount(null); clearCanvas(); }}
              className="btn-secondary"
            >
              Voltar
            </button>
          </div>

          <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-100">
            <p className="text-xs text-blue-700">
              <strong>Nota:</strong> Esta é uma assinatura eletrônica simples para confirmação do consumo mensal,
              não uma assinatura digital certificada (ICP-Brasil).
            </p>
          </div>
        </>
      )}
    </div>
  );
}
