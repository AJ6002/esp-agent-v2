"""Tier 0.5 Local Semantic Vector Router for ESP APM.

Provides sub-5ms intent classification for natural phrasing variations
and semantic paraphrasing without calling remote LLMs.
Uses TF-IDF n-gram vectorization and cosine similarity against curated intent anchors.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.schemas.esp_diagnosis import ESPIntentEnum

logger = logging.getLogger("agent.semantic_router")


@dataclass(frozen=True)
class SemanticMatchResult:
    intent: ESPIntentEnum
    confidence: float
    matched_anchor: str
    cosine_similarity: float
    is_confident: bool


# Curated Intent Exemplar Anchors across Domains 1, 2, 9, 10, Safety, and Knowledge
INTENT_ANCHORS: dict[ESPIntentEnum, list[str]] = {
    ESPIntentEnum.FLEET_INVENTORY: [
        "what is the current status of the fleet",
        "how many wells are running and tripped",
        "show active producing wells and stopped wells",
        "fleet inventory breakdown by gathering cluster",
        "list all operating esp units in the field",
        "which wells are online right now",
        "fleet overview and well status count",
        "operational state of all monitored wells",
        "show all wells in cluster and field",
    ],
    ESPIntentEnum.FLEET_PRODUCTION: [
        "how much oil are we producing across the field",
        "total gross liquid extraction rate in barrels per day",
        "what is our current daily production output",
        "deferred oil and production loss across gathering stations",
        "what are we lifting right now in bopd and bpd",
        "overall field output and production efficiency",
        "how much liquid is being pumped today",
        "total field barrel rate and deferment volume",
        "daily oil yield across all wells",
        "total gross liquid rate and net oil produced",
        "daily extraction volume in barrels",
        "total extraction volume across the field",
        "extraction volume in barrels",
    ],
    ESPIntentEnum.FLEET_TRIAGE: [
        "which wells should we restore or fix first",
        "triage priority ranking for offline assets",
        "most critical wells needing maintenance intervention",
        "prioritize tripped wells by deferred revenue impact",
        "urgency matrix for downed pumps",
        "which tripped wells are highest priority to service",
        "rank offline wells for maintenance team dispatch",
        "which asset needs immediate workover or repair",
    ],
    ESPIntentEnum.FLEET_EXECUTIVE: [
        "give me the morning executive briefing",
        "high level management kpi summary",
        "superintendent daily operational scorecard",
        "fleet executive overview and supervisory directives",
        "management summary report for operations meeting",
        "executive briefing on field availability and revenue",
    ],
    ESPIntentEnum.FLEET_ANOMALY: [
        "which running wells are showing abnormal drift",
        "sub trip degradation and early warning signals",
        "unhealthy producing wells drifting from baseline",
        "early anomaly detection in running fleet",
        "incipient failure warnings for operating pumps",
        "wells showing vibration drift or motor temp rise",
    ],
    ESPIntentEnum.FLEET_TIMELINE: [
        "chronological trip incident timeline",
        "alarm density and event clustering across stations",
        "recent fleet trip sequence over time",
        "show historical alarm timeline and shutdown clusters",
        "frequency of trips over the past week",
    ],
    ESPIntentEnum.MULTI_WELL_COMPARE: [
        "compare telemetry between well and well",
        "side by side comparative audit of well performance",
        "contrast hydraulic and electrical data between pumps",
        "compare well vs well parameters",
        "difference in vibration and current between two wells",
    ],
    ESPIntentEnum.CLUSTER_COMPARE: [
        "compare gathering center performance",
        "benchmark cluster against cluster",
        "gathering station production and water cut comparison",
        "contrast cluster vs cluster uptime and flow rates",
        "compare gcs stations across the field",
    ],
    ESPIntentEnum.HISTORICAL_COMPARE: [
        "is the well operating within design envelope",
        "baseline audit against calibrated p50 operating limits",
        "historical baseline comparison for well telemetry",
        "check if well parameters have drifted from design model",
        "is well running normally compared to its baseline history",
    ],
    ESPIntentEnum.PEER_BENCHMARK: [
        "how does this well rank against its cluster peers",
        "peer percentile benchmark for motor temperature and amps",
        "compare well efficiency to neighbor wells in the same pad",
        "benchmark this asset against similar wells in cluster",
    ],
    ESPIntentEnum.FLEET_RANKING: [
        "rank fleet by vibration levels",
        "top wells ordered by water cut percentage",
        "leaderboard of highest motor temperature pumps",
        "sort wells by current draw and electrical load",
        "which well has the highest vibration right now",
        "fleet leaderboard sorted by metric",
    ],
    ESPIntentEnum.EVENT_DIAGNOSE: [
        "why did the well trip or shut down",
        "root cause diagnosis of trip event",
        "explain the shutdown and give recommended corrective actions",
        "what caused the electrical or mechanical trip on this well",
        "diagnose event and explain failure signature",
        "trip investigation and troubleshooting steps for well",
    ],
    ESPIntentEnum.WELL_HEALTH: [
        "is well healthy and operating normally",
        "current health score and audit envelope for well",
        "check real time health and subsystem alarms for well",
        "evaluate electrical thermal hydraulic health for well",
    ],
    ESPIntentEnum.WELL_HISTORY: [
        "show trip history and past incidents for well",
        "how many times did well fail in the last days",
        "incident history and historical alarms for well",
        "timeline of past shutdowns on well",
    ],
    ESPIntentEnum.PRODUCTION: [
        "what is the production rate for well",
        "current liquid flow rate and water cut for well",
        "how many barrels per day is well making",
    ],
    ESPIntentEnum.WORK_ORDER_DISPATCH: [
        "dispatch work order for field technician",
        "generate autonomous maintenance ticket and loto checklist",
        "create work order to inspect mechanical seal and cable",
        "stage maintenance dispatch with lockout tagout protocol",
        "schedule repair crew and generate safety checklist for well",
        "dispatch maintenance team for well trip",
    ],
    ESPIntentEnum.UI_NAVIGATION: [
        "where can I see the electrical frequency curves",
        "how do I navigate to the reports hub",
        "where is the scenario simulator screen",
        "take me to the downhole schematic view",
        "how to get to well detail page",
        "where do I find the fleet cockpit",
        "where is the formula editor",
        "what screen shows live calculations",
    ],
    ESPIntentEnum.SELF_IDENTITY: [
        "who are you and what system is this",
        "what is your role and architecture",
        "introduce yourself and your copilot capabilities",
        "what is the esp apm copilot",
    ],
    ESPIntentEnum.SELF_CAPABILITIES: [
        "what can you do and what features are supported",
        "list all your operational analytical capabilities",
        "show me everything this maintenance copilot can do",
        "what tasks can you help me perform",
    ],
    ESPIntentEnum.SELF_BOUNDARIES: [
        "can you turn off the well or change vsd speed",
        "start the well and close the choke valve",
        "directly actuate scada controls on this well",
        "shut down pump remotely",
        "stop the well operation from here",
        "restart the tripped esp unit",
        "command the variable speed drive remotely",
        "control vsd remotely",
        "remotely adjust operating frequency",
        "send remote scada command to well",
    ],
    ESPIntentEnum.SELF_FLEET_SCOPE: [
        "which specific wells and fields do you monitor",
        "what is the boundary of your monitored asset scope",
        "can you analyze well xyz in another basin",
        "how many assets are in your database",
    ],
    ESPIntentEnum.SELF_LIMITATIONS: [
        "what are your operational limitations and edge cases",
        "disclose known constraints and sensor gaps",
        "what are you not able to do",
    ],
    ESPIntentEnum.KNOWLEDGE: [
        "what causes gas locking in an electric submersible pump",
        "api rp 11s standards for esp cable installation",
        "how does high viscosity fluid impact impeller head and flow rate",
        "explain pump off and underload shutdown mechanics",
        "what is the recommended operating range ror for esp",
        "difference between electrical leakage and phase imbalance",
    ],
}


class SemanticIntentRouter:
    """Zero-network, sub-5ms intent classifier based on TF-IDF cosine similarity."""

    def __init__(self, confidence_threshold: float = 0.35):
        self.threshold = confidence_threshold
        self._corpus: list[str] = []
        self._labels: list[ESPIntentEnum] = []
        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
            lowercase=True,
            stop_words="english",
        )
        self._fitted_vectors = None
        self._build_index()

    def _normalize_text(self, text: str) -> str:
        """Normalize asset IDs and special tokens to generic entities."""
        # Normalize wells (e.g. FS-004, FNW-001 -> 'well')
        t = re.sub(r"\b(FS|FNW|FWS)[-_]?\d+\b", "well", text, flags=re.I)
        # Normalize clusters (e.g. Cluster 15, GCS-15 -> 'cluster')
        t = re.sub(r"\b(?:GCS[-_\s]?|cluster[-_\s]?)(15|3|4)\b", "cluster", t, flags=re.I)
        # Normalize event codes (e.g. EV-20261012-103435... -> 'event')
        t = re.sub(r"\bEV-[\w\-]+\b", "event", t, flags=re.I)
        # Normalize punctuation
        t = re.sub(r"[^\w\s]", " ", t)
        return " ".join(t.lower().split())

    def _build_index(self) -> None:
        """Index all canonical anchor exemplars."""
        self._corpus = []
        self._labels = []
        for intent, phrases in INTENT_ANCHORS.items():
            for phrase in phrases:
                norm_phrase = self._normalize_text(phrase)
                self._corpus.append(norm_phrase)
                self._labels.append(intent)

        self._fitted_vectors = self._vectorizer.fit_transform(self._corpus)
        logger.info(
            f"Initialized Tier 0.5 Semantic Router: {len(self._corpus)} anchors indexed across {len(INTENT_ANCHORS)} intents."
        )

    def match(self, query: str) -> Optional[SemanticMatchResult]:
        """Classify query using cosine similarity against exemplar anchors.

        Returns:
            SemanticMatchResult if max cosine similarity >= threshold, else None.
        """
        if not query or not query.strip():
            return None

        norm_q = self._normalize_text(query)
        q_vec = self._vectorizer.transform([norm_q])
        sims = cosine_similarity(q_vec, self._fitted_vectors)[0]

        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])
        best_intent = self._labels[best_idx]
        matched_anchor = self._corpus[best_idx]

        is_confident = best_sim >= self.threshold

        logger.debug(
            f"Tier 0.5 Match: '{query}' -> {best_intent.value} (sim={best_sim:.3f}, thresh={self.threshold}, confident={is_confident})"
        )

        if is_confident:
            return SemanticMatchResult(
                intent=best_intent,
                confidence=round(min(0.98, max(0.65, best_sim + 0.15)), 2),
                matched_anchor=matched_anchor,
                cosine_similarity=round(best_sim, 3),
                is_confident=True,
            )

        return None


# Global singleton router
semantic_router = SemanticIntentRouter(confidence_threshold=0.52)
