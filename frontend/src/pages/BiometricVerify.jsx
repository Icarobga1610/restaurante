import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { monthlyAccounts as maApi, biometrics as bioApi, paymentMethods as paymentMethodsApi } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'react-toastify';
import {
  Fingerprint, Shield, CheckCircle, ArrowLeft, XCircle,
  User, Calendar, DollarSign, AlertTriangle, Info,
  Smartphone,
} from 'lucide-react';

const STATUS_MAP = {
  open: { label: 'Em Aberto', class: 'badge-yellow' },
  closed: { label: 'Fechada', class: 'badge-blue' },
  confirmed_by_biometrics: { label: 'Confirmada por Biometria', class: 'badge-purple' },
  paid: { label: 'Paga', class: 'badge-green' },
  overdue: { label: 'Vencida', class: 'badge-red' },
};

export default function BiometricVerify() {
  const navigate = useNavigate();
  const location = useLocation();
  const accountData = location.state?.account;
  const autoPay = !!location.state?.autoPay;
  const { hasRole } = useAuth();

  const [loading, setLoading] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(accountData || null);
  const [step, setStep] = useState('select'); // select, scan, result
  const [scanProgress, setScanProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [clientName, setClientName] = useState('');
  const [enrolledClients, setEnrolledClients] = useState([]);

  useEffect(() => {
    if (!accountData) {
      // Load accounts that need biometric verification
      Promise.all([
        maApi.list({ status: 'closed' }),
        bioApi.profiles.list({ active_only: true, limit: 200 }),
      ]).then(([accRes, profRes]) => {
        // Only show accounts that don't yet have biometric verification
        const unverified = accRes.data.filter((a) => !a.biometric_verification_id);
        setAccounts(unverified);
        setEnrolledClients(profRes.data);
      }).catch(() => {});
    } else {
      // Load enrolled clients for verification
      bioApi.profiles.list({ active_only: true, limit: 200 }).then((res) => {
        setEnrolledClients(res.data);
      }).catch(() => {});
    }
  }, []);

  const isEnrolled = (clientId) => {
    return enrolledClients.some((p) => p.client_id === clientId && p.is_active);
  };

  const startVerification = async () => {
    if (!selectedAccount) {
      toast.warning('Selecione uma conta mensal');
      return;
    }
    if (!isEnrolled(selectedAccount.client_id)) {
      toast.warning('Cliente não possui cadastro biométrico. Faça o cadastro primeiro.');
      return;
    }

    setStep('scan');
    setScanProgress(0);
    setResult(null);

    // Simulate fingerprint scan progress (demo mode)
    const interval = setInterval(() => {
      setScanProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 150);

    // In demo mode, simulate the scan taking ~1.5 seconds
    setLoading(true);
    try {
      // Call the biometric verify API (demo mode)
      const response = await maApi.biometricVerify(selectedAccount.id);
      clearInterval(interval);
      setScanProgress(100);

      await new Promise((r) => setTimeout(r, 400)); // brief pause to show 100%

      setResult({
        success: true,
        message: response.data?.message || 'Digital verificada com sucesso!',
      });
      toast.success('✅ Biometria confirmada!');
      if (autoPay && selectedAccount?.id) {
        try {
          const methods = await paymentMethodsApi.list();
          const main = methods.data.find((method) => method.is_default) || methods.data[0];
          await maApi.pay(selectedAccount.id, { payment_method: main?.code || 'pix' });
          toast.success('Pagamento registrado automaticamente após biometria.');
          setTimeout(() => navigate('/monthly-accounts'), 600);
        } catch (payErr) {
          toast.error(payErr.response?.data?.detail || 'Biometria ok, mas pagamento não registrado.');
        }
      }
    } catch (err) {
      clearInterval(interval);
      setResult({
        success: false,
        message: err.response?.data?.detail || 'Erro na verificação biométrica',
      });
      toast.error('❌ ' + (err.response?.data?.detail || 'Erro na verificação'));
    } finally {
      setLoading(false);
      setStep('result');
    }
  };

  const reset = () => {
    setStep('select');
    setScanProgress(0);
    setResult(null);
    setSelectedAccount(null);
  };

  const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

  return (
    <div className="max-w-3xl mx-auto animate-fade-in">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/monthly-accounts')} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft size={20} className="text-gray-600" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Confirmação Biométrica</h1>
          <p className="text-gray-500 text-sm mt-1">
            Verificação por impressão digital para confirmação de conta mensal
          </p>
        </div>
      </div>

      {/* Step 1: Select Account */}
      {step === 'select' && (
        <>
          {!accountData && !selectedAccount && (
            <div className="card mb-6">
              <h2 className="font-semibold text-gray-700 mb-3">Selecione a conta para confirmar</h2>
              <div className="space-y-2">
                {accounts.map((acc) => {
                  const enrolled = isEnrolled(acc.client_id);
                  return (
                    <button
                      key={acc.id}
                      onClick={() => {
                        setSelectedAccount(acc);
                        setClientName(acc.client_name);
                      }}
                      className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-all"
                    >
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="font-medium text-gray-800">{acc.client_name}</p>
                          <p className="text-sm text-gray-500">
                            {months[acc.month - 1]} {acc.year} — R$ {acc.total.toFixed(2)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          {!enrolled && (
                            <span className="text-xs text-amber-600 flex items-center gap-1">
                              <AlertTriangle size={12} />
                              Sem cadastro
                            </span>
                          )}
                          <Fingerprint size={18} className={enrolled ? 'text-primary-500' : 'text-gray-300'} />
                        </div>
                      </div>
                    </button>
                  );
                })}
                {accounts.length === 0 && (
                  <div className="text-center py-8">
                    <Fingerprint className="mx-auto text-gray-300" size={40} />
                    <p className="text-gray-500 mt-3">Nenhuma conta pendente de confirmação biométrica</p>
                    <p className="text-xs text-gray-400 mt-1">
                      Feche contas mensais primeiro para poder confirmá-las com biometria
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {selectedAccount && (
            <>
              {/* Account Info */}
              <div className="card mb-6 bg-primary-50 border-primary-100">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-primary-100 rounded-xl">
                    <Fingerprint size={24} className="text-primary-600" />
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

              {/* Biometric Status */}
              {isEnrolled(selectedAccount.client_id) ? (
                <div className="card mb-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-green-100 rounded-lg">
                      <Shield size={20} className="text-green-600" />
                    </div>
                    <div>
                      <h2 className="font-semibold text-gray-700">Cliente cadastrado</h2>
                      <p className="text-sm text-gray-500">Digital já registrada. Pronto para verificar.</p>
                    </div>
                  </div>

                  {/* Demo Mode Info */}
                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-100 mb-4">
                    <div className="flex items-start gap-2">
                      <Smartphone size={16} className="text-blue-500 mt-0.5" />
                      <p className="text-xs text-blue-700">
                        <strong>Modo Demo:</strong> Como não há leitor de impressão digital conectado,
                        a verificação está sendo simulada. Na produção, o cliente encostará o dedo
                        no leitor biométrico.
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={startVerification}
                    disabled={loading}
                    className="btn-primary flex items-center gap-2 w-full justify-center py-3 text-lg"
                  >
                    <Fingerprint size={24} />
                    Iniciar Verificação Biométrica
                  </button>
                </div>
              ) : (
                <div className="card mb-6 border-amber-200">
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-amber-100 rounded-lg">
                      <AlertTriangle size={20} className="text-amber-600" />
                    </div>
                    <div>
                      <h2 className="font-semibold text-gray-700">Cadastro biométrico necessário</h2>
                      <p className="text-sm text-gray-500 mt-1">
                        Este cliente ainda não possui cadastro biométrico.
                        É necessário cadastrar a digital do cliente antes de verificar.
                      </p>
                      <button
                        onClick={() => navigate('/clients', { state: { enrollBiometric: selectedAccount.client_id } })}
                        className="mt-3 btn-primary flex items-center gap-2 text-sm"
                      >
                        <Fingerprint size={16} />
                        Cadastrar Digital
                      </button>
                    </div>
                  </div>
                </div>
              )}

              <button
                onClick={() => { setSelectedAccount(null); }}
                className="btn-secondary w-full"
              >
                Voltar
              </button>
            </>
          )}
        </>
      )}

      {/* Step 2: Scanning */}
      {step === 'scan' && (
        <div className="card text-center py-12 animate-fade-in">
          <div className="mb-6">
            <div className="w-24 h-24 mx-auto rounded-full bg-primary-100 flex items-center justify-center animate-pulse">
              <Fingerprint size={48} className="text-primary-600" />
            </div>
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Verificando Digital</h2>
          <p className="text-gray-500 mb-6">Cliente: <strong>{selectedAccount?.client_name}</strong></p>

          <div className="max-w-md mx-auto mb-4">
            <div className="bg-gray-100 rounded-full h-3 overflow-hidden">
              <div
                className="h-full bg-primary-500 rounded-full transition-all duration-200 ease-out"
                style={{ width: `${scanProgress}%` }}
              />
            </div>
            <p className="text-sm text-gray-400 mt-2">{scanProgress}%</p>
          </div>

          <p className="text-xs text-gray-400">
            {scanProgress < 50
              ? 'Aguardando captura da digital...'
              : scanProgress < 80
              ? 'Processando template biométrico...'
              : scanProgress < 100
              ? 'Comparando com cadastro...'
              : 'Verificação concluída!'}
          </p>
        </div>
      )}

      {/* Step 3: Result */}
      {step === 'result' && (
        <div className={`card text-center py-12 animate-fade-in ${result?.success ? 'border-green-200' : 'border-red-200'}`}>
          <div className="mb-6">
            <div className={`w-24 h-24 mx-auto rounded-full flex items-center justify-center ${
              result?.success ? 'bg-green-100' : 'bg-red-100'
            }`}>
              {result?.success ? (
                <CheckCircle size={48} className="text-green-600" />
              ) : (
                <XCircle size={48} className="text-red-600" />
              )}
            </div>
          </div>
          <h2 className={`text-xl font-bold mb-2 ${
            result?.success ? 'text-green-700' : 'text-red-700'
          }`}>
            {result?.success ? '✅ Digital Verificada!' : '❌ Verificação Falhou'}
          </h2>
          <p className="text-gray-600 mb-2">{result?.message}</p>
          {result?.success && (
            <p className="text-sm text-gray-500">
              Conta de <strong>{selectedAccount?.client_name}</strong> confirmada por biometria.
            </p>
          )}

          <div className="flex gap-3 mt-8 justify-center">
            {result?.success ? (
              <button
                onClick={() => navigate('/monthly-accounts')}
                className="btn-primary flex items-center gap-2"
              >
                <CheckCircle size={18} />
                Ir para Contas Mensais
              </button>
            ) : (
              <button
                onClick={startVerification}
                className="btn-primary flex items-center gap-2"
              >
                <Fingerprint size={18} />
                Tentar Novamente
              </button>
            )}
            <button onClick={reset} className="btn-secondary">
              Verificar Outra Conta
            </button>
          </div>
        </div>
      )}

      {/* Consent notice */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-100">
        <div className="flex items-start gap-2">
          <Info size={16} className="text-blue-500 mt-0.5" />
          <p className="text-xs text-blue-700">
            <strong>Privacidade:</strong> Nenhuma imagem ou foto de digital é armazenada.
            Apenas um template/token criptografado é salvo. O consentimento do cliente
            é registrado em conformidade com a LGPD. A biometria é utilizada exclusivamente
            para confirmação do fechamento mensal.
          </p>
        </div>
      </div>
    </div>
  );
}
