import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { AuthProvider, useAuth } from './hooks/useAuth';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Clients from './pages/Clients';
import ClientForm from './pages/ClientForm';
import Products from './pages/Products';
import ProductForm from './pages/ProductForm';
import Ingredients from './pages/Ingredients';
import RecipeSheets from './pages/RecipeSheets';
import Orders from './pages/Orders';
import OrderForm from './pages/OrderForm';
import MonthlyAccounts from './pages/MonthlyAccounts';
import BiometricVerify from './pages/BiometricVerify';
import Delivery from './pages/Delivery';
import CashBook from './pages/CashBook';
import PaymentMethods from './pages/PaymentMethods';
import Reports from './pages/Reports';
import AuditLogs from './pages/AuditLogs';
import Companies from './pages/Companies';
import Operations from './pages/Operations';
import Management from './pages/Management';
import RoleProtectedRoute from './components/RoleProtectedRoute';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="operations" element={<Operations />} />
        <Route path="management" element={<Management />} />
        <Route path="clients" element={<Clients />} />
        <Route
          path="companies"
          element={
            <RoleProtectedRoute allowed={['admin', 'financial']}>
              <Companies />
            </RoleProtectedRoute>
          }
        />
        <Route
          path="clients/new"
          element={
            <RoleProtectedRoute allowed={['admin', 'attendant', 'financial']}>
              <ClientForm />
            </RoleProtectedRoute>
          }
        />
        <Route
          path="clients/:id/edit"
          element={
            <RoleProtectedRoute allowed={['admin', 'attendant', 'financial']}>
              <ClientForm />
            </RoleProtectedRoute>
          }
        />
        <Route path="products" element={<Products />} />
        <Route
          path="ingredients"
          element={
            <RoleProtectedRoute allowed={['admin', 'financial']}>
              <Ingredients />
            </RoleProtectedRoute>
          }
        />
        <Route
          path="recipes"
          element={
            <RoleProtectedRoute allowed={['admin', 'financial']}>
              <RecipeSheets />
            </RoleProtectedRoute>
          }
        />
        <Route
          path="products/new"
          element={
            <RoleProtectedRoute allowed={['admin', 'financial']}>
              <ProductForm />
            </RoleProtectedRoute>
          }
        />
        <Route
          path="products/:id/edit"
          element={
            <RoleProtectedRoute allowed={['admin', 'financial']}>
              <ProductForm />
            </RoleProtectedRoute>
          }
        />
        <Route path="orders" element={<Orders />} />
        <Route
          path="orders/new"
          element={
            <RoleProtectedRoute allowed={['admin', 'attendant', 'financial']}>
              <OrderForm />
            </RoleProtectedRoute>
          }
        />
        <Route path="monthly-accounts" element={<MonthlyAccounts />} />
        <Route path="biometric" element={<BiometricVerify />} />
        <Route path="delivery" element={<Delivery />} />
        <Route
          path="cash-book"
          element={
            <RoleProtectedRoute allowed={['admin', 'financial']}>
              <CashBook />
            </RoleProtectedRoute>
          }
        />
        <Route
          path="payment-methods"
          element={
            <RoleProtectedRoute allowed={['admin', 'financial']}>
              <PaymentMethods />
            </RoleProtectedRoute>
          }
        />
        <Route path="signature" element={<Navigate to="/biometric" replace />} />
        <Route path="reports" element={<Reports />} />
        <Route
          path="audit"
          element={
            <RoleProtectedRoute allowed={['admin']}>
              <AuditLogs />
            </RoleProtectedRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        pauseOnFocusLoss={false}
        draggable
        theme="colored"
      />
    </AuthProvider>
  );
}
