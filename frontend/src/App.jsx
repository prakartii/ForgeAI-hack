import React, { useState } from 'react';
import { Layout } from './components/Layout';
import { useHealth } from './hooks/useHealth';
import { OverviewPage } from './pages/OverviewPage';
import { AgentRunsPage } from './pages/AgentRunsPage';
import { GraphPage } from './pages/GraphPage';
import { FailuresPage } from './pages/FailuresPage';
import { PrismEvidencePage } from './pages/PrismEvidencePage';
import { BehaviorAbiPage } from './pages/BehaviorAbiPage';
import { HardeningPage } from './pages/HardeningPage';
import { RegressionPage } from './pages/RegressionPage';
import { ComparisonPage } from './pages/ComparisonPage';
import { ReleaseGatePage } from './pages/ReleaseGatePage';

export default function App() {
  const [currentTab, setCurrentTab] = useState('overview');
  const { health, loading, error, refresh } = useHealth(10000);

  const renderPage = () => {
    switch (currentTab) {
      case 'overview':
        return <OverviewPage health={health} />;
      case 'runs':
        return <AgentRunsPage />;
      case 'graph':
        return <GraphPage />;
      case 'failures':
        return <FailuresPage />;
      case 'prism':
        return <PrismEvidencePage />;
      case 'abi':
        return <BehaviorAbiPage />;
      case 'hardening':
        return <HardeningPage />;
      case 'regression':
        return <RegressionPage />;
      case 'comparison':
        return <ComparisonPage />;
      case 'gate':
        return <ReleaseGatePage />;
      default:
        return <OverviewPage health={health} />;
    }
  };

  return (
    <Layout
      currentTab={currentTab}
      onSelectTab={setCurrentTab}
      health={health}
      loading={loading}
      error={error}
      onRefresh={refresh}
    >
      {renderPage()}
    </Layout>
  );
}
