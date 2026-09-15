import React, { useEffect, useRef, useState } from 'react';
import { fetchClaimOptions, resolveImageUrl, submitCustomClaim } from '../../services/api';
import { PortalButton, PortalHeader } from '../ui';

const initialForm = {
  vehicle_make: '',
  vehicle_model: '',
  peril: '',
  damage_part: '',
  damage_severity: '',
  description: '',
  repair_estimate_inr: '',
  policy_tier: 'standard',
};

export function NewClaimPage({ onBack, onCreated }) {
  const [options, setOptions] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [photo, setPhoto] = useState(null);
  const [preview, setPreview] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchClaimOptions().then(setOptions).catch(() => setOptions(null));
  }, []);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handlePhoto = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPhoto(file);
    setPreview(URL.createObjectURL(file));
  };

  const isValid = form.vehicle_make && form.vehicle_model && form.peril && form.damage_part
    && form.damage_severity && form.repair_estimate_inr;

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const claim = await submitCustomClaim({ ...form, photo });
      setError(null);
      onCreated({ ...claim, image_url: resolveImageUrl(claim.image_url) });
    } catch (err) {
      setError('Something went wrong creating your claim. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!options) {
    return (
      <div className="flex-1 flex flex-col">
        <PortalHeader title="New claim" onBack={onBack} />
        <p className="px-5 text-[13px] text-pinkfaint">Loading form…</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      <PortalHeader title="Tell us what happened" onBack={onBack} />

      <div className="px-5 flex-1 space-y-4 pb-4">
        <button
          onClick={() => fileInputRef.current?.click()}
          className="w-full rounded-2xl border-2 border-dashed border-pline hover:border-pinkfaint aspect-[4/3] flex items-center justify-center overflow-hidden bg-pcream"
        >
          {preview ? (
            <img src={preview} alt="Your upload" className="w-full h-full object-cover" />
          ) : (
            <div className="text-center px-6">
              <p className="text-2xl mb-1">📷</p>
              <p className="text-[13px] font-medium text-pink">Add a photo of the damage</p>
              <p className="text-[11px] text-pinkfaint mt-1">Speeds up your review — a human still checks every photo</p>
            </div>
          )}
        </button>
        <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handlePhoto} />

        <div className="grid grid-cols-2 gap-3">
          <label className="text-[12px]">
            <span className="block text-pinkfaint mb-1">Vehicle make</span>
            <input value={form.vehicle_make} onChange={update('vehicle_make')} placeholder="Tata"
              className="w-full rounded-xl border border-pline px-3 py-2.5 text-[14px] focus:border-pteal focus:outline-none" />
          </label>
          <label className="text-[12px]">
            <span className="block text-pinkfaint mb-1">Model</span>
            <input value={form.vehicle_model} onChange={update('vehicle_model')} placeholder="Punch"
              className="w-full rounded-xl border border-pline px-3 py-2.5 text-[14px] focus:border-pteal focus:outline-none" />
          </label>
        </div>

        <label className="text-[12px] block">
          <span className="block text-pinkfaint mb-1">What happened?</span>
          <select value={form.peril} onChange={update('peril')}
            className="w-full rounded-xl border border-pline px-3 py-2.5 text-[14px] bg-white focus:border-pteal focus:outline-none">
            <option value="" disabled>Select an incident type</option>
            {options.perils.map((p) => <option key={p} value={p}>{p.charAt(0) + p.slice(1).toLowerCase()}</option>)}
          </select>
        </label>

        <div className="grid grid-cols-2 gap-3">
          <label className="text-[12px]">
            <span className="block text-pinkfaint mb-1">Damaged part</span>
            <select value={form.damage_part} onChange={update('damage_part')}
              className="w-full rounded-xl border border-pline px-3 py-2.5 text-[14px] bg-white focus:border-pteal focus:outline-none">
              <option value="" disabled>Select</option>
              {options.damage_parts.map((p) => <option key={p} value={p}>{p.replace(/_/g, ' ').toLowerCase()}</option>)}
            </select>
          </label>
          <label className="text-[12px]">
            <span className="block text-pinkfaint mb-1">Severity</span>
            <select value={form.damage_severity} onChange={update('damage_severity')}
              className="w-full rounded-xl border border-pline px-3 py-2.5 text-[14px] bg-white focus:border-pteal focus:outline-none">
              <option value="" disabled>Select</option>
              {options.damage_severities.map((s) => <option key={s} value={s}>{s.charAt(0) + s.slice(1).toLowerCase()}</option>)}
            </select>
          </label>
        </div>

        <label className="text-[12px] block">
          <span className="block text-pinkfaint mb-1">Describe what happened</span>
          <textarea value={form.description} onChange={update('description')} rows={3}
            placeholder="A brief description helps us process your claim faster."
            className="w-full rounded-xl border border-pline px-3 py-2.5 text-[14px] focus:border-pteal focus:outline-none resize-none" />
        </label>

        <label className="text-[12px] block">
          <span className="block text-pinkfaint mb-1">Estimated repair cost (₹)</span>
          <input type="number" value={form.repair_estimate_inr} onChange={update('repair_estimate_inr')} placeholder="15000"
            className="w-full rounded-xl border border-pline px-3 py-2.5 text-[14px] focus:border-pteal focus:outline-none" />
        </label>

        <label className="text-[12px] block">
          <span className="block text-pinkfaint mb-1">Your policy</span>
          <div className="grid grid-cols-3 gap-2">
            {options.policy_tiers.map((tier) => (
              <button
                key={tier.id}
                onClick={() => setForm((f) => ({ ...f, policy_tier: tier.id }))}
                className={`rounded-xl border px-2 py-2.5 text-center transition-colors ${
                  form.policy_tier === tier.id ? 'border-pteal bg-pteal-50' : 'border-pline'
                }`}
              >
                <p className="text-[12px] font-semibold capitalize">{tier.id}</p>
                <p className="text-[10px] text-pinkfaint mt-0.5">₹{tier.deductible.toLocaleString('en-IN')} excess</p>
              </button>
            ))}
          </div>
        </label>

        {error && <p className="text-[13px] text-pcoral-700 bg-pcoral-50 rounded-lg px-3 py-2">{error}</p>}
      </div>

      <div className="px-5 pb-6 pt-2">
        <PortalButton onClick={handleSubmit} loading={submitting} disabled={!isValid}>
          Continue
        </PortalButton>
      </div>
    </div>
  );
}
