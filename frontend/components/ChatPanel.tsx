"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Sparkles } from "lucide-react";
import {
  converse,
  emptyBrief,
  type ConversationMessage,
  type TripBrief,
  type BriefLeg,
} from "@/lib/api";

interface Props {
  // Called when the brief is ready and the user chooses to plan it.
  onPlanReady: (legs: BriefLeg[], brief: TripBrief) => void;
}

export function ChatPanel({ onPlanReady }: Props) {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [brief, setBrief] = useState<TripBrief>(emptyBrief());
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;

    const nextMessages: ConversationMessage[] = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await converse({ messages: nextMessages, brief });
      setMessages([...nextMessages, { role: "assistant", content: res.reply }]);
      setBrief(res.brief);
    } catch {
      setError("Couldn't reach the planner. Try again in a moment.");
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  const showEmptyState = messages.length === 0;

  return (
    <div className="flex flex-col h-[70vh] bg-card border border-line rounded-xl overflow-hidden">
      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {showEmptyState && (
          <div className="h-full flex flex-col items-center justify-center text-center text-ink-soft px-6">
            <Sparkles size={28} className="text-route mb-3" />
            <p className="font-medium text-ink">Tell me about your trip</p>
            <p className="text-sm mt-1 max-w-sm">
              Where you&apos;re starting from, who&apos;s coming, the kind of place you&apos;re after —
              or just say you&apos;re not sure and I&apos;ll suggest a few ideas.
            </p>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div
              className={
                m.role === "user"
                  ? "bg-route text-white rounded-2xl rounded-br-sm px-4 py-2.5 max-w-[80%] text-sm"
                  : "bg-paper border border-line rounded-2xl rounded-bl-sm px-4 py-2.5 max-w-[80%] text-sm"
              }
            >
              {m.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-paper border border-line rounded-2xl rounded-bl-sm px-4 py-3">
              <Loader2 size={16} className="animate-spin text-ink-soft" />
            </div>
          </div>
        )}
      </div>

      {/* Ready-to-plan banner */}
      {brief.ready && brief.proposed_legs.length > 0 && (
        <div className="border-t border-line bg-route-soft px-4 py-3 flex items-center justify-between gap-3">
          <div className="text-sm">
            <span className="font-medium text-route">Ready to plan</span>
            <span className="text-ink-soft">
              {" "}
              — {brief.proposed_legs.length} leg{brief.proposed_legs.length > 1 ? "s" : ""}
              {brief.destinations.length > 0 && `: ${brief.destinations.join(", ")}`}
            </span>
          </div>
          <button
            onClick={() => onPlanReady(brief.proposed_legs, brief)}
            className="bg-route text-white text-sm font-medium px-4 py-2 rounded-lg hover:opacity-90 shrink-0"
          >
            Plan this trip
          </button>
        </div>
      )}

      {error && (
        <div className="border-t border-line bg-amber-soft px-4 py-2 text-sm text-amber">{error}</div>
      )}

      {/* Input */}
      <div className="border-t border-line p-3 flex items-end gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Type your message..."
          rows={1}
          className="flex-1 resize-none border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-route/30 max-h-32"
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="bg-route text-white p-2.5 rounded-lg hover:opacity-90 disabled:opacity-40 shrink-0"
          aria-label="Send"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}