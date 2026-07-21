"use client";

import { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Send, Sparkles } from "lucide-react";
import {
  converse,
  emptyBrief,
  type ConversationMessage,
  type TripBrief,
  type BriefLeg,
} from "@/lib/api";

interface Props {
  onPlanReady: (legs: BriefLeg[], brief: TripBrief) => void;
}

const glass = {
  background: "rgba(255,255,255,0.09)",
  backdropFilter: "blur(16px)",
  border: "0.5px solid rgba(255,255,255,0.16)",
};

function TypingDots() {
  return (
    <div className="flex items-center gap-1.5 px-1">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="w-1.5 h-1.5 rounded-full"
          style={{ background: "rgba(255,255,255,0.6)" }}
          animate={{ y: [0, -5, 0] }}
          transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.15, ease: "easeInOut" }}
        />
      ))}
    </div>
  );
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
    <div
      className="flex flex-col h-[520px] max-h-[65vh] rounded-3xl overflow-hidden"
      style={{ ...glass, boxShadow: "0 24px 48px -16px rgba(20,10,35,0.5), inset 0 1px 0 rgba(255,255,255,0.1)" }}
    >
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3">
        {showEmptyState && (
          <div className="h-full flex flex-col items-center justify-center text-center px-6">
            <Sparkles size={28} style={{ color: "#F0B87A" }} className="mb-3" />
            <p className="font-medium text-white">Tell me about your trip</p>
            <p className="text-sm mt-1 max-w-sm text-white/60">
              Where you&apos;re starting from, who&apos;s coming, the kind of place you&apos;re after —
              or just say you&apos;re not sure and I&apos;ll suggest a few ideas.
            </p>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 14, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.32, ease: "easeOut" }}
              className={m.role === "user" ? "flex justify-end" : "flex justify-start"}
            >
              <div
                className={
                  m.role === "user"
                    ? "rounded-2xl rounded-br-sm px-4 py-2.5 max-w-[80%] text-sm text-[#3A1F0A] font-medium"
                    : "rounded-2xl rounded-bl-sm px-4 py-2.5 max-w-[80%] text-sm text-white"
                }
                style={
                  m.role === "user"
                    ? { background: "linear-gradient(135deg, #F0B87A, #D97A4A)" }
                    : { background: "rgba(255,255,255,0.10)", border: "0.5px solid rgba(255,255,255,0.14)" }
                }
              >
                {m.content}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <div className="rounded-2xl rounded-bl-sm px-4 py-3" style={{ background: "rgba(255,255,255,0.10)" }}>
              <TypingDots />
            </div>
          </motion.div>
        )}
      </div>

      {brief.ready && brief.proposed_legs.length > 0 && (
        <div className="px-4 py-3 flex items-center justify-between gap-3" style={{ borderTop: "0.5px solid rgba(255,255,255,0.14)", background: "rgba(240,184,122,0.12)" }}>
          <div className="text-sm">
            <span className="font-medium" style={{ color: "#F0B87A" }}>Ready to plan</span>
            <span className="text-white/60">
              {" "}
              — {brief.proposed_legs.length} leg{brief.proposed_legs.length > 1 ? "s" : ""}
              {brief.destinations.length > 0 && `: ${brief.destinations.join(", ")}`}
            </span>
          </div>
          <button
            onClick={() => onPlanReady(brief.proposed_legs, brief)}
            className="text-sm font-medium px-4 py-2 rounded-lg hover:opacity-90 shrink-0 text-[#3A1F0A]"
            style={{ background: "linear-gradient(135deg, #F0B87A, #D97A4A)" }}
          >
            Plan this trip
          </button>
        </div>
      )}

      {error && (
        <div className="px-4 py-2 text-sm text-white/80" style={{ borderTop: "0.5px solid rgba(255,255,255,0.14)", background: "rgba(232,157,168,0.15)" }}>
          {error}
        </div>
      )}

      <div className="p-3 flex items-end gap-2" style={{ borderTop: "0.5px solid rgba(255,255,255,0.14)" }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Type your message..."
          rows={1}
          className="flex-1 resize-none rounded-lg px-3 py-2 text-sm text-white placeholder-white/40 focus:outline-none max-h-32"
          style={{ background: "rgba(255,255,255,0.08)", border: "0.5px solid rgba(255,255,255,0.16)" }}
        />
        <motion.button
          onClick={send}
          disabled={loading || !input.trim()}
          whileTap={{ scale: 0.92 }}
          className="p-2.5 rounded-lg hover:opacity-90 disabled:opacity-30 shrink-0 text-[#3A1F0A]"
          style={{ background: "linear-gradient(135deg, #F0B87A, #D97A4A)" }}
          aria-label="Send"
        >
          <Send size={18} />
        </motion.button>
      </div>
    </div>
  );
}