"use client";

import { useState } from "react";
import { Plus, Trash2, Loader2 } from "lucide-react";
import type { LegInput, TravelMode } from "@/lib/api";

const MODES: { value: TravelMode; label: string }[] = [
  { value: "flight", label: "Flight" },
  { value: "train", label: "Train" },
  { value: "bus", label: "Bus" },
  { value: "driving", label: "Driving" },
];

interface Props {
  onSubmit: (params: {
    legs: LegInput[];
    departDate: string;
    adults: number;
    children: number;
    elders: number;
    hasPets: boolean;
    budgetInr: number | null;
  }) => void;
  loading: boolean;
}

export function TripPlannerForm({ onSubmit, loading }: Props) {
  const [legs, setLegs] = useState<LegInput[]>([
    { mode: "flight", origin: "", destination: "" },
  ]);
  const [departDate, setDepartDate] = useState("");
  const [adults, setAdults] = useState(1);
  const [children, setChildren] = useState(0);
  const [elders, setElders] = useState(0);
  const [hasPets, setHasPets] = useState(false);
  const [budget, setBudget] = useState("");

  function updateLeg(index: number, patch: Partial<LegInput>) {
    setLegs((prev) => prev.map((leg, i) => (i === index ? { ...leg, ...patch } : leg)));
  }

  function addLeg() {
    const last = legs[legs.length - 1];
    setLegs((prev) => [...prev, { mode: "driving", origin: last?.destination ?? "", destination: "" }]);
  }

  function removeLeg(index: number) {
    setLegs((prev) => prev.filter((_, i) => i !== index));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!departDate || legs.some((l) => !l.origin || !l.destination)) return;
    const budgetInr = budget.trim() ? Number(budget) : null;
    onSubmit({ legs, departDate, adults, children, elders, hasPets, budgetInr });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-3">
        {legs.map((leg, i) => (
          <div key={i} className="flex flex-wrap items-center gap-2 bg-card border border-line rounded-lg p-3">
            <span className="font-mono text-xs w-6 text-ink-soft">{String(i + 1).padStart(2, "0")}</span>
            <select
              value={leg.mode}
              onChange={(e) => updateLeg(i, { mode: e.target.value as TravelMode })}
              className="border border-line rounded-md px-2 py-1.5 text-sm bg-paper"
            >
              {MODES.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Origin"
              value={leg.origin}
              onChange={(e) => updateLeg(i, { origin: e.target.value })}
              className="flex-1 min-w-[120px] border border-line rounded-md px-3 py-1.5 text-sm"
              required
            />
            <span className="text-ink-soft">&rarr;</span>
            <input
              type="text"
              placeholder="Destination"
              value={leg.destination}
              onChange={(e) => updateLeg(i, { destination: e.target.value })}
              className="flex-1 min-w-[120px] border border-line rounded-md px-3 py-1.5 text-sm"
              required
            />
            {legs.length > 1 && (
              <button
                type="button"
                onClick={() => removeLeg(i)}
                className="text-ink-soft hover:text-amber p-1"
                aria-label="Remove leg"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>
        ))}

        <button
          type="button"
          onClick={addLeg}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-route hover:underline"
        >
          <Plus size={16} /> Add another leg
        </button>
      </div>

      <div className="flex flex-wrap gap-3 items-end bg-card border border-line rounded-lg p-3">
        <label className="text-sm">
          <span className="block text-xs text-ink-soft mb-1">Depart date</span>
          <input
            type="date"
            value={departDate}
            onChange={(e) => setDepartDate(e.target.value)}
            className="border border-line rounded-md px-2 py-1.5 text-sm"
            required
          />
        </label>
        <label className="text-sm">
          <span className="block text-xs text-ink-soft mb-1">Adults</span>
          <input
            type="number"
            min={1}
            value={adults}
            onChange={(e) => setAdults(Number(e.target.value))}
            className="border border-line rounded-md px-2 py-1.5 text-sm w-16"
          />
        </label>
        <label className="text-sm">
          <span className="block text-xs text-ink-soft mb-1">Children</span>
          <input
            type="number"
            min={0}
            value={children}
            onChange={(e) => setChildren(Number(e.target.value))}
            className="border border-line rounded-md px-2 py-1.5 text-sm w-16"
          />
        </label>
        <label className="text-sm">
          <span className="block text-xs text-ink-soft mb-1">Elders</span>
          <input
            type="number"
            min={0}
            value={elders}
            onChange={(e) => setElders(Number(e.target.value))}
            className="border border-line rounded-md px-2 py-1.5 text-sm w-16"
          />
        </label>
        <label className="text-sm">
          <span className="block text-xs text-ink-soft mb-1">Budget (INR, optional)</span>
          <input
            type="number"
            min={0}
            placeholder="e.g. 15000"
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            className="border border-line rounded-md px-2 py-1.5 text-sm w-32"
          />
        </label>
        <label className="flex items-center gap-1.5 text-sm pb-1.5">
          <input type="checkbox" checked={hasPets} onChange={(e) => setHasPets(e.target.checked)} />
          Traveling with pets
        </label>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="inline-flex items-center gap-2 bg-route text-white font-medium px-5 py-2.5 rounded-lg hover:opacity-90 disabled:opacity-50 transition"
      >
        {loading && <Loader2 size={16} className="animate-spin" />}
        {loading ? "Planning..." : "Plan trip"}
      </button>
    </form>
  );
}