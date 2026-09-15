import React, { useState } from 'react';
import { Layout } from './components/Layout';
import { useHealth } from './hooks/useHealth';
import { JudgeViewPage } from './pages/JudgeViewPage';
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

// A portal action (e.g. filing a claim, running the fairness check) can
// link straight into this console pre-filtered to what it just did --
// e.g. /?view=runs&claim_id=USER_abc123 -- so a viewer can verify the
// portal's result against the real trace, not just trust it.
const initialParams = new URLSearchParams(window.location.search);

export default function App() {
  const [currentTab, setCurrentTab] = useState(initialParams.get('view') || 'overview');
  const { health, loading, error, refresh } = useHealth(10000);

  const renderPage = () => {
    switch (currentTab) {
      case 'judge':
        return <JudgeViewPage onNavigate={setCurrentTab} />;
      case 'overview':
        return <OverviewPage health={health} />;
      case 'runs':
        return <AgentRunsPage initialClaimId={initialParams.get('claim_id') || undefined} />;
      case 'graph':
        return <GraphPage />;
      case 'failures':
        return <FailuresPage initialFailureId={initialParams.get('failure_id') || undefined} />;
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
