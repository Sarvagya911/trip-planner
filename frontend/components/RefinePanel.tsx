"use client";

import { useState } from "react";
import { Loader2, Send, Wand2 } from "lucide-react";
import {
  converse,
  type ConversationMessage,
  type TripBrief,
  type BriefLeg,
} from "@/lib/api";

interface Props {
  brief: TripBrief;
  messages: ConversationMessage[];
  onReplan: (legs: BriefLeg[], brief: TripBrief, messages: ConversationMessage[]) => void;
}

const QUICK_ACTIONS = [
  "Make it cheaper",
  "Make it faster",
  "Add a night",
  "Avoid flights",
];

export function RefinePanel({ brief, messages, onReplan }: Props) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refine(text: string) {
    const request = text.trim();
    if (!request || loading) return;

    setLoading(true);
    setError(null);
    setNote(null);

    const nextMessages: ConversationMessage[] = [
      ...messages,
      { role: "user", content: request },
    ];

    try {
      const res = await converse({ messages: nextMessages, brief: brief });
      const updated = res.brief;
      const withReply: ConversationMessage[] = [
        ...nextMessages,
        { role: "assistant", content: res.reply },
      ];
      setNote(res.reply);
      setInput("");
      if (updated.ready && updated.proposed_legs.length > 0) {
        onReplan(updated.proposed_legs, updated, withReply);
      }
    } catch {
      setError("Couldn't update the trip. Try again in a moment.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-8 border-t border-line pt-6">
      <div className="flex items-center gap-2 mb-3">
        <Wand2 size={16} className="text-route" />
        <h2 className="text-sm font-semibold">Refine this trip</h2>
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action}
            onClick={() => refine(action)}
            disabled={loading}
            className="text-sm border border-line rounded-full px-3 py-1.5 hover:bg-route-soft hover:border-route/40 disabled:opacity-40 transition"
          >
            {action}
          </button>
        ))}
      </div>

      <div className="flex items-end gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              refine(input);
            }
          }}
          placeholder="Or ask for a change — 'remove the bus', 'I have a dog'..."
          className="flex-1 border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-route/30"
          disabled={loading}
        />
        <button
          onClick={() => refine(input)}
          disabled={loading || !input.trim()}
          className="bg-route text-white p-2.5 rounded-lg hover:opacity-90 disabled:opacity-40 shrink-0"
          aria-label="Send change"
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
        </button>
      </div>

      {loading && (
        <p className="text-sm text-ink-soft mt-3">Updating your trip...</p>
      )}
      {note && !loading && (
        <p className="text-sm text-ink-soft mt-3 bg-route-soft border border-route/20 rounded-lg px-3 py-2">
          {note}
        </p>
      )}
      {error && (
        <p className="text-sm text-amber mt-3">{error}</p>
      )}
    </div>
  );
}