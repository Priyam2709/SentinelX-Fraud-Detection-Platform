import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ExecutiveDashboard from './pages/ExecutiveDashboard';
import TransactionExplorer from './pages/TransactionExplorer';
import FraudInvestigation from './pages/FraudInvestigation';
import ExplainableAI from './pages/ExplainableAI';
import ModelMonitoring from './pages/ModelMonitoring';
import NetworkGraph from './pages/NetworkGraph';
import { alertAPI } from './api';

export default function App() {
  const [openAlertCount, setOpenAlertCount] = useState(0);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    fetchAlertCount();
    const interval = setInterval(fetchAlertCount, 8000);
    return () => clearInterval(interval);
  }, [refreshTrigger]);

  const fetchAlertCount = async () => {
    try {
      const data = await alertAPI.list({ status_filter: 'OPEN', limit: 1 });
      setOpenAlertCount(data.total || 0);
    } catch (e) {
      // offline / mock fallback
    }
  };

  const handleDataRefreshed = () => {
    setRefreshTrigger((prev) => prev + 1);
    fetchAlertCount();
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 flex flex-col text-slate-100">
        {/* Top Header */}
        <Navbar onDataRefreshed={handleDataRefreshed} />

        <div className="flex-1 flex overflow-hidden">
          {/* Left Navigation Sidebar */}
          <Sidebar openAlertCount={openAlertCount} />

          {/* Main Dashboard Canvas */}
          <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-[1600px] mx-auto w-full">
            <Routes>
              <Route path="/" element={<ExecutiveDashboard refreshTrigger={refreshTrigger} />} />
              <Route path="/transactions" element={<TransactionExplorer refreshTrigger={refreshTrigger} />} />
              <Route path="/investigations" element={<FraudInvestigation refreshTrigger={refreshTrigger} />} />
              <Route path="/explainable-ai" element={<ExplainableAI refreshTrigger={refreshTrigger} />} />
              <Route path="/models" element={<ModelMonitoring refreshTrigger={refreshTrigger} />} />
              <Route path="/network" element={<NetworkGraph refreshTrigger={refreshTrigger} />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
