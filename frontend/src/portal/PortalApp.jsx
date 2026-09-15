import React, { useState } from 'react';
import { PortalShell } from './ui';
import { HomePage } from './pages/HomePage';
import { NewClaimPage } from './pages/NewClaimPage';
import { ClaimReviewPage } from './pages/ClaimReviewPage';
import { ResultPage } from './pages/ResultPage';
import { FairnessCheckPage } from './pages/FairnessCheckPage';

export function PortalApp() {
  const [view, setView] = useState('home');
  const [claim, setClaim] = useState(null);
  const [result, setResult] = useState(null);

  return (
    <PortalShell>
      {view === 'home' && (
        <HomePage
          onPickClaim={(c) => { setClaim(c); setView('claim'); }}
          onStartNewClaim={() => setView('newClaim')}
          onOpenFairnessCheck={() => setView('fairness')}
        />
      )}
      {view === 'newClaim' && (
        <NewClaimPage
          onBack={() => setView('home')}
          onCreated={(c) => { setClaim(c); setView('claim'); }}
        />
      )}
      {view === 'claim' && (
        <ClaimReviewPage
          claim={claim}
          onBack={() => setView('home')}
          onSubmitted={(r) => { setResult(r); setView('result'); }}
        />
      )}
      {view === 'result' && (
        <ResultPage
          result={result}
          onRestart={() => setView('home')}
          onOpenFairnessCheck={() => setView('fairness')}
        />
      )}
      {view === 'fairness' && (
        <FairnessCheckPage onBack={() => setView('home')} />
      )}
    </PortalShell>
  );
}
