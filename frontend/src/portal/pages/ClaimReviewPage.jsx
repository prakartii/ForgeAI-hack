import React, { useState } from 'react';
import { submitClaim } from '../../services/api';
import { PortalButton, PortalHeader } from '../ui';

export function ClaimReviewPage({ claim, onBack, onSubmitted }) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleFile = async () => {
    setSubmitting(true);
    try {
      const result = await submitClaim({ claimId: claim.claim_id, protected: true });
      setError(null);
      onSubmitted(result);
    } catch (err) {
      setError('Something went wrong submitting your claim. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <PortalHeader title="Review your claim" onBack={onBack} />

      <div className="px-5 flex-1 space-y-4">
        {claim.image_url && (
          <div className="rounded-2xl overflow-hidden aspect-[4/3] bg-pcream">
            <img src={claim.image_url} alt="Damage photo" className="w-full h-full object-cover" />
          </div>
        )}

        <div className="rounded-2xl border border-pline p-4 space-y-3">
          <div className="flex justify-between text-[13px]">
            <span className="text-pinkfaint">Vehicle</span>
            <span className="font-medium">{claim.vehicle_make} {claim.vehicle_model}</span>
          </div>
          <div className="flex justify-between text-[13px]">
            <span className="text-pinkfaint">Incident</span>
            <span className="font-medium">{claim.peril?.toLowerCase()}</span>
          </div>
          <div className="flex justify-between text-[13px]">
            <span className="text-pinkfaint">Damage</span>
            <span className="font-medium">{claim.damage_part?.replace(/_/g, ' ').toLowerCase()}</span>
          </div>
          {claim.description && (
            <p className="text-[13px] text-pink pt-1 border-t border-pline leading-relaxed">{claim.description}</p>
          )}
        </div>

        {error && <p className="text-[13px] text-pcoral-700 bg-pcoral-50 rounded-lg px-3 py-2">{error}</p>}
      </div>

      <div className="px-5 pb-6 pt-4">
        <PortalButton onClick={handleFile} loading={submitting}>
          File this claim
        </PortalButton>
      </div>
    </div>
  );
}
