"""Seed threat-intelligence material and word-window chunking."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDocument:
    source: str
    text: str


DOCUMENTS = [
    SourceDocument(
        "CISA: Ransomware response",
        """Ransomware incidents often begin with stolen credentials, exposed remote access, or a vulnerable internet-facing service. Threat actors may move laterally before encrypting systems, and some also steal data for extortion. Defenders should isolate affected hosts, preserve volatile evidence where practical, and notify the incident response team. Keep known-good backups offline or immutable and verify that they can be restored. Reset credentials from a clean device, revoke active sessions, and review identity-provider and remote-access logs for unusual authentication. Do not reconnect rebuilt systems until the entry point is understood and security controls are improved. Report suspected incidents through the organization's established response channels and applicable government reporting process. Recovery should include monitoring for persistence and testing restored systems before returning them to production.""",
    ),
    SourceDocument(
        "CISA: Phishing and account compromise",
        """Phishing messages use impersonation, urgency, or unexpected attachments to persuade a recipient to disclose a password or approve a sign-in. Modern campaigns may use convincing business language and links to lookalike login pages. Organizations can reduce risk with phishing-resistant multifactor authentication, conditional access, and user reporting channels. When a user reports a suspicious message, preserve the message headers and URLs, search for related deliveries, and remove confirmed malicious copies. For a suspected account compromise, revoke sessions and tokens, reset credentials, inspect mailbox forwarding rules, and review sign-in events. A password reset alone may not end an attack if an attacker still has a session token or an application grant. Share verified indicators with the security team and avoid opening suspicious attachments during triage.""",
    ),
    SourceDocument(
        "MITRE ATT&CK: Command and control",
        """Command and control describes communication between an adversary-controlled system and compromised devices. An operator may use web protocols, DNS, or encrypted channels to blend traffic into normal activity. A single domain lookup is not proof of compromise, so analysts correlate destination reputation, process ancestry, connection timing, certificate details, and endpoint alerts. Network defenders can use egress controls, DNS logging, proxy telemetry, and endpoint detection to identify unusual patterns. Hunt for rare destinations contacted by many hosts, unexpected periodic connections, and interpreters launching network utilities. Preserve relevant timestamps and host context before blocking infrastructure so investigations retain useful evidence. Indicators should be assessed for freshness and confidence because infrastructure can be shared or reassigned.""",
    ),
    SourceDocument(
        "NIST: Vulnerability management",
        """A vulnerability management program discovers, prioritizes, and remediates weaknesses across an organization's technology. Asset inventory and exposure context matter: an internet-facing system that handles sensitive data may deserve faster attention than an isolated test host. Teams should use trusted advisories and vulnerability identifiers, confirm affected product versions, and evaluate whether exploitation is known or observed. Apply vendor updates or mitigations through a tested change process, then verify the fix with rescanning. When immediate patching is not possible, reduce exposure with compensating controls and document an owner and deadline. Security teams should communicate risk in operational terms and revisit priorities as threat intelligence and asset criticality change.""",
    ),
    SourceDocument(
        "CISA: Indicators of compromise",
        """Indicators of compromise can include file hashes, domains, IP addresses, email artifacts, and behavioral patterns. An indicator is a clue rather than a verdict: shared hosting, cloud services, and recycled infrastructure can cause false positives. Analysts should record the source, collection time, confidence, and context for every indicator. Validate a match with independent telemetry such as endpoint process activity, authentication records, or DNS history. Use short-lived indicators carefully and favor durable behaviors for longer-term detection. Before distributing indicators, remove sensitive personal data and follow organizational sharing rules. Track expiry or review dates so stale indicators do not create unnecessary blocks. A useful threat-intelligence report explains what was observed, how certain the assessment is, and what action a defender can take.""",
    ),
]


def chunk_text(text: str, words_per_chunk: int = 100, overlap: int = 20) -> list[str]:
    """Split text into bounded word windows with a small continuity overlap."""
    if words_per_chunk <= 0 or overlap < 0 or overlap >= words_per_chunk:
        raise ValueError("Require words_per_chunk > overlap >= 0")
    words = text.split()
    step = words_per_chunk - overlap
    return [" ".join(words[start : start + words_per_chunk]) for start in range(0, len(words), step)]


def get_chunks() -> list[dict[str, str]]:
    chunks = []
    for document in DOCUMENTS:
        chunks.extend(
            {"text": text, "source": document.source}
            for text in chunk_text(document.text)
        )
    return chunks
