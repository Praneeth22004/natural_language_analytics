import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import QueryInspectorModal from './components/QueryInspectorModal';
import IncidentDetailModal from './components/IncidentDetailModal';

import ChatAssistantPage from './pages/ChatAssistantPage';
import IncidentAnalyticsDashboardPage from './pages/IncidentAnalyticsDashboardPage';
import RecurringAndRcaPage from './pages/RecurringAndRcaPage';
import OutageInvestigationPage from './pages/OutageInvestigationPage';
import ExecutiveReportsPage from './pages/ExecutiveReportsPage';
import AdminSettingsPage from './pages/AdminSettingsPage';

import { fetchSettings } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [theme, setTheme] = useState('dark');
  const [systemMode, setSystemMode] = useState('Enterprise Simulation');
  
  // Modals
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [inspectorData, setInspectorData] = useState(null);
  const [lastQuery, setLastQuery] = useState(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    async function checkStatus() {
      try {
        const res = await fetchSettings();
        setSystemMode(res.mode || 'Enterprise Simulation');
      } catch (err) {
        setSystemMode('Offline Fallback');
      }
    }
    checkStatus();
  }, []);

  const handleInspectQuery = (data) => {
    setInspectorData(data);
    setLastQuery(data);
  };

  return (
    <div className="app-container">
      {/* Navigation Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemMode={systemMode}
      />

      {/* Main Content Viewport */}
      <div className="main-content">
        <Navbar
          activeTab={activeTab}
          onOpenQueryInspector={() => setInspectorData(lastQuery)}
          lastQuery={lastQuery}
          theme={theme}
          setTheme={setTheme}
        />

        {/* Dynamic Pages */}
        {activeTab === 'chat' && (
          <ChatAssistantPage
            onInspectQuery={handleInspectQuery}
            onSelectIncident={(inc) => setSelectedIncident(inc)}
          />
        )}

        {activeTab === 'dashboard' && (
          <IncidentAnalyticsDashboardPage
            onSelectIncident={(inc) => setSelectedIncident(inc)}
          />
        )}

        {activeTab === 'recurring' && (
          <RecurringAndRcaPage
            onSelectIncident={(inc) => setSelectedIncident(inc)}
          />
        )}

        {activeTab === 'outage' && (
          <OutageInvestigationPage />
        )}

        {activeTab === 'reports' && (
          <ExecutiveReportsPage />
        )}

        {activeTab === 'settings' && (
          <AdminSettingsPage />
        )}
      </div>

      {/* Query Inspector Modal */}
      <QueryInspectorModal
        isOpen={Boolean(inspectorData)}
        onClose={() => setInspectorData(null)}
        queryData={inspectorData}
      />

      {/* Incident Detail / AI Post-Mortem Modal */}
      <IncidentDetailModal
        isOpen={Boolean(selectedIncident)}
        onClose={() => setSelectedIncident(null)}
        incident={selectedIncident}
      />
    </div>
  );
}
