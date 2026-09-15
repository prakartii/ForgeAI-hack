import React, { useEffect, useState } from 'react';
import { fetchRandomClaim, fetchSampleClaims, resolveImageUrl } from '../../services/api';
import { ClaimCard, PortalButton } from '../ui';

export function HomePage({ onPickClaim, onStartNewClaim, onOpenFairnessCheck }) {
  const [claims, setClaims] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [totalClaims, setTotalClaims] = useState(null);
  const [drawingRandom, setDrawingRandom] = useState(false);

  useEffect(() => {
    fetchSampleClaims()
      .then((data) => setClaims(data.map((c) => ({ ...c, image_url: resolveImageUrl(c.image_url) }))))
      .catch(() => setClaims([]))
      .finally(() => setLoading(false));
  }, []);

  const handleRandom = async () => {
    setDrawingRandom(true);
    try {
      const claim = await fetchRandomClaim();
      setTotalClaims(claim.total_claims_in_system);
      onPickClaim({ ...claim, image_url: resolveImageUrl(claim.image_url) });
    } catch (err) {
      // stay on this page; the sample list below still works
    } finally {
      setDrawingRandom(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col px-5 pb-6">
      <div className="pt-2 pb-5">
        <p className="text-[11px] tracking-wide text-pteal font-semibold">FairClaim</p>
        <h1 className="font-portal text-2xl font-extrabold leading-tight mt-1">File a claim</h1>
        <p className="text-[13px] text-pinkfaint mt-1.5 leading-relaxed">
          Upload a photo and a few details, and we'll review it the same way a real claim gets reviewed.
        </p>
      </div>

      <PortalButton onClick={onStartNewClaim} className="mb-3">
        📷 File a new claim
      </PortalButton>
      <PortalButton variant="secondary" onClick={handleRandom} loading={drawingRandom} className="mb-6">
        🎲 Try a random real claim{totalClaims ? ` (1 of ${totalClaims.toLocaleString('en-IN')})` : ''}
      </PortalButton>

      <div className="flex items-center gap-3 mb-4">
        <div className="h-px bg-pline flex-1" />
        <p className="text-[11px] text-pinkfaint">or pick a sample accident</p>
        <div className="h-px bg-pline flex-1" />
      </div>

      <div className="flex-1 space-y-2.5">
        {loading ? (
          <p className="text-[13px] text-pinkfaint">Loading sample claims…</p>
        ) : (
          claims.map((claim) => (
            <ClaimCard
              key={claim.claim_id}
              claim={claim}
              selected={selected?.claim_id === claim.claim_id}
              onClick={() => setSelected(claim)}
            />
          ))
        )}
      </div>

      <div className="pt-5 space-y-3">
        <PortalButton variant="secondary" disabled={!selected} onClick={() => onPickClaim(selected)}>
          Continue with sample
        </PortalButton>
        <PortalButton variant="ghost" onClick={onOpenFairnessCheck}>
          Try the fairness check instead →
        </PortalButton>
      </div>
    </div>
  );
}
