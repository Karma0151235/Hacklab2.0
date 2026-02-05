"use client";

import { SentimentOutput } from "@/lib/types/api";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface SentimentCardProps {
  sentiment: SentimentOutput;
}

export function SentimentCard({ sentiment }: SentimentCardProps) {
  const sentimentColors = {
    positive: {
      badge: "bg-green-500/20 text-green-400 border-green-500/30",
      bar: "bg-green-500",
      label: "POSITIVE",
    },
    neutral: {
      badge: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
      bar: "bg-yellow-500",
      label: "NEUTRAL",
    },
    negative: {
      badge: "bg-red-500/20 text-red-400 border-red-500/30",
      bar: "bg-red-500",
      label: "NEGATIVE",
    },
  };

  const colors =
    sentimentColors[
      sentiment.overall_sentiment as keyof typeof sentimentColors
    ] || sentimentColors.neutral;

  // Calculate bar width: score ranges from -1.0 to 1.0, convert to 0-100%
  const barWidth = (sentiment.sentiment_score + 1) * 50;

  // Trend icon
  const getTrendIcon = () => {
    switch (sentiment.trend) {
      case "improving":
        return <TrendingUp className="h-3.5 w-3.5 text-green-400" />;
      case "declining":
        return <TrendingDown className="h-3.5 w-3.5 text-red-400" />;
      default:
        return <Minus className="h-3.5 w-3.5 text-gray-400" />;
    }
  };

  return (
    <div className="rounded-lg border border-blue-500/30 bg-blue-950/20 p-4 space-y-3">
      {/* Header with title and sentiment badge */}
      <div className="flex items-start justify-between">
        <h4 className="font-medium text-sm text-gray-100">Market Sentiment</h4>
        <div
          className={cn(
            "px-2.5 py-1 rounded-full text-xs font-semibold border",
            colors.badge,
          )}
        >
          {colors.label}
        </div>
      </div>

      {/* Sentiment Score Bar */}
      <div className="space-y-1">
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-400">Score</span>
          <span className="text-xs font-mono font-medium text-gray-300">
            {sentiment.sentiment_score.toFixed(2)}
          </span>
        </div>
        <div className="h-2 w-full rounded-full bg-gray-800 overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-300",
              colors.bar,
            )}
            style={{ width: `${barWidth}%` }}
          />
        </div>
      </div>

      {/* Confidence and Articles */}
      <div className="grid grid-cols-2 gap-3 pt-1">
        <div>
          <div className="text-[10px] uppercase tracking-wide text-gray-500 mb-1">
            Confidence
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-1.5 w-12 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-400 rounded-full"
                style={{ width: `${sentiment.confidence * 100}%` }}
              />
            </div>
            <span className="text-xs font-medium text-gray-300">
              {Math.round(sentiment.confidence * 100)}%
            </span>
          </div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wide text-gray-500 mb-1">
            Articles
          </div>
          <div className="text-sm font-medium text-gray-300">
            {sentiment.articles_analyzed}
          </div>
        </div>
      </div>

      {/* Summary */}
      {sentiment.summary && (
        <div className="rounded bg-gray-800/50 p-3 border border-gray-700">
          <p className="text-xs leading-relaxed text-gray-300">
            {sentiment.summary}
          </p>
        </div>
      )}

      {/* Trend Info */}
      {sentiment.trend && (
        <div className="flex items-center gap-2 pt-1">
          <div className="flex items-center gap-1.5">
            {getTrendIcon()}
            <div>
              <span className="text-xs text-gray-500">Trend: </span>
              <span className="text-xs font-medium text-gray-300 capitalize">
                {sentiment.trend}
              </span>
            </div>
          </div>
        </div>
      )}

      {sentiment.trend_explanation && (
        <p className="text-xs text-gray-400 italic pt-1">
          {sentiment.trend_explanation}
        </p>
      )}
    </div>
  );
}
