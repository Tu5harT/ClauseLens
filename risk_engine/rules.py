"""Explainable rule lexicon: risk categories, weighted regex patterns, advice."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Rule:
    pattern: "re.Pattern"
    weight: float
    reason: str


@dataclass
class Category:
    name: str
    advice: str
    rules: List[Rule]
    gate: Optional["re.Pattern"] = None  # clause must match this for the category to apply
    description: str = ""
    counter: str = ""  # fairer wording to propose


def _r(pattern: str, weight: float, reason: str) -> Rule:
    return Rule(re.compile(pattern, re.IGNORECASE | re.DOTALL), weight, reason)


def _g(pattern: str) -> "re.Pattern":
    return re.compile(pattern, re.IGNORECASE)


CATEGORIES: List[Category] = [
    Category(
        "Liability & Indemnification",
        "Negotiate a mutual, capped liability (e.g. fees paid in the last 12 months) and limit indemnity to third-party claims caused by the indemnifying party.",
        [
            _r(r"\b(unlimited|uncapped)\b|liability (shall|will|is) not be limited|without (any )?(limit|cap)", 0.7, "Liability appears uncapped or unlimited"),
            _r(r"indemnif(y|ies|ication)|hold harmless", 0.45, "Indemnification / hold-harmless obligation"),
            _r(r"(solely|exclusively|fully) (liable|responsible)|sole (liability|responsibility)", 0.45, "Sole liability placed on one party"),
            _r(r"liquidated damages|penalt(y|ies)", 0.4, "Penalty / liquidated damages exposure"),
            _r(r"(including|and) (reasonable )?attorneys?'? fees", 0.25, "Obligation to cover legal fees"),
            _r(r"in no event (shall|will) (the )?(company|provider|licensor|vendor|supplier|us|we)\b.{0,40}liable", 0.35, "Liability disclaimed by one party only"),
        ],
        description="Who pays when something goes wrong, and how much.",
    ),
    Category(
        "Payment Terms",
        "Seek reasonable payment windows (net 30), capped late fees, and written notice before any fee change.",
        [
            _r(r"non-?refundable|no refunds?|not (be )?refund", 0.5, "Payments are non-refundable"),
            _r(r"(late|interest)\s*(fee|charge|payment)?s?.{0,60}\d+(\.\d+)?\s*%|\d+(\.\d+)?\s*%\s*(per|a|each)\s*(month|week|day)", 0.5, "High late-payment interest or fee"),
            _r(r"(due|payable|paid)\s+(immediately|upon receipt|on demand|within\s+(\d|[1-7]|one|two|three|five|seven)\s*(\(\d+\)\s*)?(business\s+)?days?)", 0.4, "Very short payment window"),
            _r(r"(increase|adjust|change|revise)\s+(the\s+)?(fees?|prices?|rates?|charges?)\b", 0.45, "Fees can be changed after signing"),
            _r(r"set-?off|withhold (any )?(amounts?|payments?)|deduct", 0.3, "Right to deduct or set off payments"),
            _r(r"(early|cancellation|termination) fee", 0.4, "Fee triggered by cancelling"),
            _r(r"minimum (commitment|purchase|spend|fee)", 0.35, "Minimum spend commitment"),
        ],
        gate=_g(r"pay|fee|invoice|price|charge|refund|cost|amount|\$|usd|inr|eur"),
        description="Prices, invoicing, penalties and refunds.",
    ),
    Category(
        "Termination",
        "Ask for mutual termination rights, a reasonable notice period (30+ days) and a cure period for breaches.",
        [
            _r(r"terminat\w*.{0,80}(without (prior )?notice|immediately|at any time)|(without (prior )?notice|immediately).{0,60}terminat", 0.55, "Termination without notice or at any time"),
            _r(r"terminat\w*.{0,60}(for convenience|without cause|for any reason)", 0.4, "Termination without cause allowed"),
            _r(r"(may not|shall not|cannot|no right to) (terminate|cancel)", 0.55, "Restricts your ability to terminate"),
            _r(r"(sole|absolute) discretion.{0,60}terminat|terminat\w*.{0,60}(sole|absolute) discretion", 0.5, "Termination at sole discretion of one party"),
            _r(r"terminat\w*.{0,100}(forfeit|lose|no longer entitled|remain (liable|payable))", 0.35, "Consequences that survive termination"),
        ],
        gate=_g(r"terminat|cancel|expire|expiry"),
        description="How and when the agreement can end.",
    ),
    Category(
        "Auto-Renewal",
        "Calendar the opt-out deadline, request a shorter renewal term, and require a reminder notice before renewal.",
        [
            _r(r"automatic(ally)?\s+(renew|extend)|auto-?renew|evergreen", 0.65, "Contract renews automatically"),
            _r(r"successive\s+(terms?|periods?|renewal)", 0.4, "Rolls into successive terms"),
            _r(r"unless.{0,80}(written\s+)?notice.{0,60}(\d{2,3}|sixty|ninety|thirty)\s*(\(\d+\)\s*)?days?\s+(prior|before)", 0.35, "Opt-out requires notice well before renewal"),
            _r(r"renew\w*.{0,60}(same|then-current)\s+(term|length|period)", 0.3, "Renews for a full term"),
        ],
        gate=_g(r"renew|extend|evergreen"),
        description="Contracts that silently continue.",
    ),
    Category(
        "Confidentiality",
        "Limit confidentiality to a fixed period (2-5 years), define 'Confidential Information' narrowly, and make the duty mutual.",
        [
            _r(r"any and all (information|data|materials)|all information (disclosed|provided)", 0.4, "Over-broad definition of confidential information"),
            _r(r"in perpetuity|perpetual|indefinite(ly)?|survive.{0,40}(termination|expiration)", 0.4, "Confidentiality obligation has no end date"),
            _r(r"injunctive relief|irreparable (harm|injury)", 0.3, "Pre-agreed injunctive relief"),
            _r(r"liquidated damages|penalt(y|ies)|\$\s?\d[\d,]*.{0,30}(per|each)\s+(breach|violation|disclosure)", 0.45, "Financial penalty for disclosure"),
        ],
        gate=_g(r"confidential|non-?disclosure|proprietary|trade secret"),
        description="What you may not share, and for how long.",
    ),
    Category(
        "Intellectual Property",
        "Keep ownership of pre-existing IP, grant only a limited licence, and avoid assigning rights to work outside the project scope.",
        [
            _r(r"(assign|transfer)s?.{0,60}(all|any|entire).{0,60}(right|title|interest)", 0.55, "Full assignment of IP rights"),
            _r(r"work(s)?\s+(made\s+)?for\s+hire", 0.35, "Work-for-hire clause"),
            _r(r"irrevocabl\w+.{0,60}(licen[sc]e|right)|(licen[sc]e|right).{0,60}irrevocabl", 0.5, "Irrevocable licence granted"),
            _r(r"(perpetual|worldwide|royalty-?free).{0,60}(licen[sc]e)|(licen[sc]e).{0,60}(perpetual|worldwide|royalty-?free)", 0.4, "Broad perpetual / worldwide licence"),
            _r(r"waive.{0,30}moral rights", 0.3, "Moral rights waived"),
            _r(r"all (intellectual property|inventions|ideas|work product).{0,80}(shall be|is|are|will be)\s+(the\s+)?(sole|exclusive)?\s*(property|owned)", 0.45, "All work product owned by the other party"),
        ],
        gate=_g(r"intellectual property|copyright|patent|trademark|licen[sc]e|invention|work product|ownership|moral rights|for hire"),
        description="Who owns what you create.",
    ),
    Category(
        "Non-Compete & Exclusivity",
        "Narrow the scope, duration and geography, or remove exclusivity; confirm enforceability in your jurisdiction.",
        [
            _r(r"non-?compet\w*|shall not (compete|engage in)|not\s+(directly\s+or\s+indirectly\s+)?(compete|be engaged)", 0.6, "Non-compete restriction"),
            _r(r"exclusiv(e|ely|ity)", 0.4, "Exclusivity obligation"),
            _r(r"non-?solicit\w*|shall not.{0,40}(solicit|hire|recruit)", 0.4, "Non-solicitation restriction"),
            _r(r"most[- ]favou?red", 0.3, "Most-favoured-customer clause"),
        ],
        description="Limits on working with others.",
    ),
    Category(
        "Dispute Resolution",
        "Prefer a neutral venue, allow court access, and keep class-action / jury rights unless there is a strong reason to waive.",
        [
            _r(r"waive.{0,60}(jury|class action|right to (sue|appeal))", 0.55, "Waiver of jury / class-action rights"),
            _r(r"(binding|mandatory)\s+arbitration|shall be (finally )?(settled|resolved) by arbitration", 0.4, "Mandatory binding arbitration"),
            _r(r"exclusive\s+(jurisdiction|venue|forum)", 0.35, "Exclusive jurisdiction in a fixed location"),
            _r(r"(bear|pay).{0,30}own (legal )?(costs|fees)|prevailing party.{0,40}(fees|costs)", 0.3, "Cost-shifting for legal disputes"),
            _r(r"governed by (and construed in accordance with )?the laws? of", 0.15, "Governing law specified (check jurisdiction)"),
        ],
        gate=_g(r"dispute|arbitrat|jurisdiction|governing law|governed by|venue|court|jury|class action|litigation"),
        description="Where and how disagreements are settled.",
    ),
    Category(
        "Warranty Disclaimer",
        "Ask for basic warranties (conformance to specification, non-infringement, professional workmanship) and a remedy for defects.",
        [
            _r(r"\bas[- ]is\b|\bas available\b", 0.5, "Provided 'as is'"),
            _r(r"disclaims?\s+(all|any)\s+(other\s+)?(express(ed)?\s+(or|and)\s+)?(implied\s+)?warrant", 0.55, "All warranties disclaimed"),
            _r(r"no\s+(express\s+or\s+implied\s+)?warrant(y|ies)|makes? no (representation|warrant)", 0.45, "No warranty offered"),
            _r(r"merchantab\w+|fitness for a particular purpose", 0.3, "Implied warranties excluded"),
            _r(r"not (responsible|liable) for.{0,60}(error|defect|interruption|loss|damage|downtime)", 0.4, "No responsibility for defects or downtime"),
        ],
        description="Promises about quality, or the lack of them.",
    ),
    Category(
        "Unilateral Changes",
        "Require written, mutual amendment (or at least 30 days' notice with a right to exit) for material changes.",
        [
            _r(r"(modify|change|amend|update|revise|alter)\w*.{0,80}(at any time|from time to time|without (prior )?(written )?notice|unilateral)", 0.6, "Terms can be changed without notice or consent"),
            _r(r"reserves? the right to.{0,40}(modify|change|amend|suspend|discontinue|revoke|alter)", 0.5, "Right to change or suspend reserved"),
            _r(r"(sole|absolute)\s+(and\s+absolute\s+)?discretion", 0.4, "Decision at one party's sole discretion"),
            _r(r"(continued use|continuing to use).{0,60}(constitutes?|deemed|acceptance)|deemed (to have )?accept", 0.35, "Acceptance implied by continued use"),
            _r(r"assign\w*.{0,40}(this agreement|its rights).{0,40}without (the )?(consent|notice)", 0.4, "Contract can be assigned without consent"),
        ],
        description="One side can rewrite the deal.",
    ),
    Category(
        "Data Privacy",
        "Limit data use to the agreed purpose, require breach notification, and prohibit sale or onward sharing without consent.",
        [
            _r(r"(sell|share|disclose|transfer|license).{0,60}(data|information).{0,60}(third[- ]part(y|ies)|affiliates|partners)", 0.55, "Data may be shared or sold to third parties"),
            _r(r"not (be )?(responsible|liable).{0,80}(breach|unauthori[sz]ed access|data loss|security incident)", 0.55, "Disclaims responsibility for breaches"),
            _r(r"retain.{0,60}(data|information).{0,60}(indefinitely|after (termination|expiration)|as long as)", 0.4, "Data retained after the contract ends"),
            _r(r"(collect|process|use).{0,40}(personal|user|customer|biometric|location)\s*(data|information)", 0.2, "Collects personal data"),
            _r(r"consent.{0,40}(deemed|implied)|waive.{0,40}privacy", 0.4, "Implied consent / privacy waiver"),
        ],
        gate=_g(r"data|privacy|personal information|gdpr|breach"),
        description="How your information is collected, used and shared.",
    ),
]

CATEGORY_BY_NAME = {c.name: c for c in CATEGORIES}


def score_category(cat: Category, text: str) -> Tuple[float, List[str]]:
    """Noisy-OR combination of matched rule weights -> (score, reasons)."""
    if cat.gate is not None and not cat.gate.search(text):
        return 0.0, []
    remaining, reasons = 1.0, []
    for rule in cat.rules:
        if rule.pattern.search(text):
            remaining *= 1.0 - rule.weight
            reasons.append(rule.reason)
    return round(1.0 - remaining, 3), reasons


COUNTERS = {
    "Liability & Indemnification": "Each party's total liability is capped at the fees paid or payable in the 12 months before the claim, and neither party is responsible for indirect or consequential loss. A duty to cover third-party claims applies only where the claim results from that party's own breach or negligence.",
    "Payment Terms": "Invoices are payable within 30 days of receipt. Any late-payment interest is simple, capped at a modest rate stated in the order form. Prices stay fixed for the initial term and change only on 60 days' written notice. Fees for services not delivered are returned.",
    "Termination": "Either party may end this Agreement on 30 days' written notice, or sooner if the other party commits a material breach and fails to fix it within 14 days of notice. The Customer pays for services delivered up to the end date.",
    "Auto-Renewal": "This Agreement renews only by written agreement of both parties. If renewal is automatic, the Provider must send a reminder 30-60 days before the opt-out deadline, and renewal terms are no longer than 12 months.",
    "Confidentiality": "Each party protects the other's clearly marked Confidential Information for 3 years after disclosure, excluding information that is public, independently developed or already known. Disclosure required by law is permitted.",
    "Intellectual Property": "Each party keeps its pre-existing IP. The Customer receives ownership of deliverables created specifically for it on full payment, and the Provider receives only a limited licence to content as needed to provide the services.",
    "Non-Compete & Exclusivity": "The Provider accepts no restriction on working with other customers. Where a limit is unavoidable it covers only direct competitors, for 6 to 12 months, in the places where services were actually provided.",
    "Dispute Resolution": "Disputes are first escalated to senior management for 30 days, then to mediation. Either party keeps the right to go to court; venue is the defendant's home jurisdiction or another mutually agreed neutral place.",
    "Warranty Disclaimer": "The Provider warrants that services will be performed with reasonable skill and care and will materially conform to the agreed specification, and will re-perform or refund non-conforming services.",
    "Unilateral Changes": "Amendments require a written document signed by both parties. If the Provider must update its standard terms, it gives 30 days' notice and the Customer may leave at no cost if the update is materially adverse.",
    "Data Privacy": "Personal data is processed only to provide the services and under written instructions. It is not sold or shared with third parties without consent. The Provider notifies the Customer of any breach within 72 hours and deletes or returns data on termination.",
}
for _c in CATEGORIES:
    _c.counter = COUNTERS[_c.name]
