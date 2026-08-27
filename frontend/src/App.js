import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';
import { Toaster } from './components/ui/sonner';
import { PeriodProvider } from './lib/period';
import { AppShell } from './components/AppShell';
import Dashboard from './pages/Dashboard';
import PemantauanStok from './pages/PemantauanStok';
import MasterReagen from './pages/MasterReagen';
import DataLIS from './pages/DataLIS';
import PRF from './pages/PRF';
import Penerimaan from './pages/Penerimaan';
import AnalisisExcel from './pages/AnalisisExcel';

function App() {
  return (
    <PeriodProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/pemantauan" element={<PemantauanStok />} />
            <Route path="/master-reagen" element={<MasterReagen />} />
            <Route path="/data-lis" element={<DataLIS />} />
            <Route path="/prf" element={<PRF />} />
            <Route path="/penerimaan" element={<Penerimaan />} />
            <Route path="/analisis-excel" element={<AnalisisExcel />} />
          </Routes>
        </AppShell>
        <Toaster position="top-right" richColors />
      </BrowserRouter>
    </PeriodProvider>
  );
}

export default App;
