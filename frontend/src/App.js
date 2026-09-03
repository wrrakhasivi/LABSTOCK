import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';
import { Toaster } from './components/ui/sonner';
import { PeriodProvider } from './lib/period';
import { AuthProvider, useAuth } from './lib/auth';
import { ThemeProvider } from './lib/theme';
import { AppShell } from './components/AppShell';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import PemantauanStok from './pages/PemantauanStok';
import MasterReagen from './pages/MasterReagen';
import DataLIS from './pages/DataLIS';
import PRF from './pages/PRF';
import Penerimaan from './pages/Penerimaan';
import AnalisisExcel from './pages/AnalisisExcel';
import Pengguna from './pages/Pengguna';
import Pengaturan from './pages/Pengaturan';
import Analitik from './pages/Analitik';

function AuthedApp() {
  return (
    <PeriodProvider>
      <AppShell>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analitik" element={<Analitik />} />
          <Route path="/pemantauan" element={<PemantauanStok />} />
          <Route path="/master-reagen" element={<MasterReagen />} />
          <Route path="/data-lis" element={<DataLIS />} />
          <Route path="/prf" element={<PRF />} />
          <Route path="/penerimaan" element={<Penerimaan />} />
          <Route path="/analisis-excel" element={<AnalisisExcel />} />
          <Route path="/pengguna" element={<Pengguna />} />
          <Route path="/pengaturan" element={<Pengaturan />} />
        </Routes>
      </AppShell>
    </PeriodProvider>
  );
}

function Gate() {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? <AuthedApp /> : <Login />;
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Gate />
          <Toaster position="top-right" richColors />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
