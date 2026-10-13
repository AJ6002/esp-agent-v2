'use client';
import { Citation, AskResult } from '@/lib/types';
import { KNOWLEDGE_CATEGORY_LABELS } from '@/lib/types';
import { Link, AlertTriangle, ChevronRight, Zap } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface SourceType {
  source_type: string;
  source_id: number;
  title: string;
  excerpt?: string;
  relevance_score: number;
  url?: string;
}

export default function CitationList({ citations }: { citations: Citation[] }) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-3 space-y-2">
      <div className="text-xs text-muted font-medium mb-1">Citations ({citations.length})</div>
      {citations.map((c, i) => (
        <CitationCard key={`${c.source_type}-${c.source_id}`} citation={c} index={i + 1} />
      ))}
    </div>
  );
}

function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  const scoreColor = citation.relevance_score > 0.7 ? 'text-green-400' : citation.relevance_score > 0.3 ? 'text-yellow-400' : 'text-gray-400';

  return (
    <a
      href={citation.url || '#'}
      target="_self"
      className="flex items-start gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors group no-underline text-inherit"
    >
      <span className="shrink-0 w-5 h-5 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center mt-0.5">
        {index}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium truncate">{citation.title}</span>
          <span className={`text-xs ${scoreColor} font-mono shrink-0`}>{Math.round(citation.relevance_score * 100)}%</span>
        </div>
        {citation.excerpt && (
          <p className="text-xs text-muted mt-0.5 line-clamp-2">{citation.excerpt}</p>
        )}
      </div>
      <ChevronRight size={14} className="shrink-0 mt-1 text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
    </a>
  );
}

export function AnswerPanel({
  result,
  loading,
  onSelectOption,
}: {
  result: AskResult | null;
  loading: boolean;
  onSelectOption?: (option: string) => void;
}) {
  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center gap-3 text-muted">
          <div className="w-4 h-4 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          <span>Retrieving knowledge base and generating answer...</span>
        </div>
      </div>
    );
  }

  if (!result) return null;

  return (
    <div className="space-y-4">
      {/* Safety disclaimer - always visible */}
      <div className="flex items-start gap-2 text-xs text-yellow-400 bg-yellow-500/10 rounded-lg p-3">
        <AlertTriangle size={14} className="shrink-0 mt-0.5" />
        <span>{result.disclaimer}</span>
      </div>

      {/* Answer */}
      <div className="card space-y-4">
        {/* Confidence & mock indicator */}
        <div className="flex items-center gap-3 text-xs">
          {result.is_mock && (
            <span className="badge bg-yellow-500/20 text-yellow-400">Mock AI Mode</span>
          )}
          <span className="text-muted">
            Confidence: <span className={result.confidence > 0.7 ? 'text-green-400' : result.confidence > 0.3 ? 'text-yellow-400' : 'text-gray-400 font-medium'}>
              {Math.round(result.confidence * 100)}%
            </span>
          </span>
          {result.confidence < 0.3 && (
            <span className="text-yellow-400">Insufficient knowledge base evidence. Verify with equipment manual and on-site inspection.</span>
          )}
        </div>

        {/* Answer text */}
        <div className="copilot-markdown-content text-sm leading-relaxed text-gray-200">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ node, ...props }) => <h1 className="text-base font-bold text-white mt-4 mb-2 pb-1 border-b border-white/10" {...props} />,
              h2: ({ node, ...props }) => <h2 className="text-sm font-semibold text-white mt-3 mb-1.5" {...props} />,
              h3: ({ node, ...props }) => <h3 className="text-xs font-semibold text-primary mt-2.5 mb-1 uppercase tracking-wider" {...props} />,
              p: ({ node, ...props }) => <p className="mb-2.5 last:mb-0 leading-relaxed text-gray-200" {...props} />,
              ul: ({ node, ...props }) => <ul className="list-disc list-inside space-y-1 mb-3 text-gray-300 ml-1" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal list-inside space-y-1 mb-3 text-gray-300 ml-1" {...props} />,
              li: ({ node, ...props }) => <li className="leading-relaxed marker:text-primary" {...props} />,
              strong: ({ node, ...props }) => <strong className="font-semibold text-white" {...props} />,
              em: ({ node, ...props }) => <em className="italic text-gray-300" {...props} />,
              code: ({ node, className, children, ...props }: any) => {
                const isBlock = className || (typeof children === 'string' && children.includes('\n'));
                if (!isBlock) {
                  return (
                    <code className="px-1.5 py-0.5 rounded bg-white/10 text-primary font-mono text-xs border border-white/10" {...props}>
                      {children}
                    </code>
                  );
                }
                return (
                  <pre className="p-3 my-2.5 rounded-lg bg-black/60 border border-white/10 font-mono text-xs overflow-x-auto text-gray-200">
                    <code className={className} {...props}>{children}</code>
                  </pre>
                );
              },
              table: ({ node, ...props }) => (
                <div className="overflow-x-auto my-3 rounded-lg border border-white/10 bg-black/20">
                  <table className="w-full text-xs text-left border-collapse" {...props} />
                </div>
              ),
              thead: ({ node, ...props }) => <thead className="bg-white/10 text-white uppercase text-[10px] tracking-wider" {...props} />,
              tbody: ({ node, ...props }) => <tbody className="divide-y divide-white/5" {...props} />,
              tr: ({ node, ...props }) => <tr className="hover:bg-white/[0.03] transition-colors" {...props} />,
              th: ({ node, ...props }) => <th className="px-3 py-2 font-semibold text-gray-300 border-b border-white/10" {...props} />,
              td: ({ node, ...props }) => <td className="px-3 py-2 text-gray-300" {...props} />,
              blockquote: ({ node, ...props }) => (
                <blockquote className="border-l-2 border-primary/50 pl-3 italic my-2 text-gray-400 bg-white/[0.02] py-1 rounded-r" {...props} />
              ),
              hr: ({ node, ...props }) => <hr className="my-4 border-white/10" {...props} />,
            }}
          >
            {result.answer}
          </ReactMarkdown>
        </div>

        {/* Suggested clarification options / follow-up chips */}
        {result.suggested_options && result.suggested_options.length > 0 && (
          <div className="pt-2 border-t border-white/10 space-y-2">
            <div className="text-xs font-semibold text-primary flex items-center gap-1.5">
              <Zap size={13} />
              <span>{result.needs_clarification ? 'Please Select an Asset or Option to Proceed:' : 'Suggested Inquiries & Next Inquiries:'}</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {result.suggested_options.map((opt, i) => (
                <button
                  key={i}
                  onClick={() => onSelectOption && onSelectOption(opt)}
                  className="px-3 py-1.5 rounded-md text-xs font-medium bg-primary/15 text-primary hover:bg-primary/25 border border-primary/30 transition-all flex items-center gap-1 text-left"
                >
                  <span>{opt}</span>
                  <ChevronRight size={12} className="opacity-70" />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Warnings */}
        {result.warnings && result.warnings.length > 0 && (
          <div className="space-y-1">
            {result.warnings.map((w, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-red-400 bg-red-500/10 rounded p-2">
                <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                <span>{w}</span>
              </div>
            ))}
          </div>
        )}
      </div>


      {/* Citations */}
      {result.citations && result.citations.length > 0 && (
        <div className="card">
          <CitationList citations={result.citations} />
        </div>
      )}

      {/* No sources warning */}
      {(!result.citations || result.citations.length === 0) && (
        <div className="card">
          <div className="flex items-start gap-2 text-sm text-yellow-400">
            <Zap size={14} className="shrink-0 mt-0.5" />
            <span>Insufficient knowledge base evidence. Verify with equipment manual and on-site inspection.</span>
          </div>
        </div>
      )}
    </div>
  );
}
