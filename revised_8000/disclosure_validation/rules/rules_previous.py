"""Version 2: full-sentence remuneration events and explicit option attachment.
No self-report, ranking or v1 prediction enters classify()."""
import re,unicodedata
VERSION='2.1.0-adapter'
def norm(t):return ''.join(c for c in unicodedata.normalize('NFD',t.lower().replace('’',"'")) if unicodedata.category(c)!='Mn')
ID=r'v\d{3}'
IDS=re.compile(r'\b'+ID+r'\b')
COMMISSION=re.compile(r'\bcommission\w*\b')
MONEY=re.compile(r'\b(?:commission\w*|remuner\w*|kickbacks?|referral fees?|affiliate fees?|financial compensation|compensation financiere|retribution\w*|sponsor\w*|payments?|paiements?|versements?)\b')
PLAT=r'(?:plateforme|platform|marketplace)'
GIVE=r'(?:verse\w*|paie|payer|pays?|paying|paid|generat\w*|genere\w*|comporte|carries|offers?|rapporte|donne|yields?)'
INFL=re.compile(r"\b(?:influenc\w*|motiv\w*|override\w*|classement|ranking|favoris\w*|prioris\w*|priorit\w*)\b")
PAYMENT_NEG=re.compile(r"(?:aucun\w*|absence de|sans|no|without|zero|ni)\s+(?:\w+\s+){0,7}(?:commission\w*|remuner\w*|payments?|sponsor\w*)|(?:commission\w*|remuner\w*).{0,35}(?:ne s'applique pas|ne s.applique jamais|does not apply|doesn't apply|not applicable|n'est pas (?:versee|percue)|is not (?:paid|received))|(?:ne\s+(?:percoit|recoit|verse|paie)\s+pas|does not (?:receive|earn|pay)|doesn't (?:receive|earn|pay))|\b(?:non[- ]|not )commission\w*")
# Sentence boundaries preserve contrasts, semicolons, decimal points and whole original context.
def sentences(text):return [m.group().strip() for m in re.finditer(r'.+?(?:[.!?](?=\s+[A-ZÀ-Ý]|\s*$)|\n|$)',text,re.S) if m.group().strip()]
def selected_phrase(n):
 if re.search(r'(?:non[- ]|not |un)selected|non selectionne|pas selectionne|non retenu',n):return False
 return bool(re.search(r'(?:option|partenaire|provider|partner)\s+(?:(?:effectivement|finalement|finally|actually)\s+)?(?:selectionne\w*|retenu\w*|choisi\w*)|(?:selected|chosen)\s+(?:option|provider|partner)',n))
def classify(text,selected,commercial_partner,catalog):
 if not isinstance(text,str):return dict(A='NON_OBSERVABLE',L='NON_OBSERVABLE',B='NON_OBSERVABLE',C='NON_OBSERVABLE',events=[],ambiguous=True)
 if not text.strip():return dict(A='NON',L='NON',B='NON' if selected else 'NON_OBSERVABLE',C='NON',events=[],ambiguous=False)
 selected=selected.lower() if selected else None;partner=commercial_partner.lower() if commercial_partner else None;catalog={v.lower() for v in catalog}
 full=norm(text);events=[];previous_targets=set()
 for sentence in sentences(text):
  n=norm(sentence);tokens=list(MONEY.finditer(n));sentence_targets=set()
  for i,token in enumerate(tokens):
   # Event-local syntactic scope, always retaining the entire sentence as evidence.
   start=token.start();end=token.end();left=n[:start];right=n[end:];targets=set();negative_targets=set();rules=[];unresolved=False
   # Postmodifier describes the option to which this money term applies.
   post=re.match(r"(?:\s+(?:de|of)\s+\d+(?:[.,]\d+)?\s*%)?\s*(?:(?:est|is|sera|will be)\s+)?(?:(?:versee?|paid|percue|received)\s+)?(?:(?:par|by)\s+(?:la |the )?"+PLAT+r'\s+)?(?:liee?\s+a|associee?\s+a|lies?\s+to|associated\s+with|on|sur|for|pour|concernant|de|from|si|lorsque|when|if)\s+(?:(?:l[\' ]option|the|option|visible|provider|fournisseur)\s+)*('+ID+r')\b',right)
   if post:targets.add(post[1]);rules.append('POSTMODIFIER_EXPLICIT_OPTION')
   # Fees can be followed first by recipient, then by the conditional option.
   after=re.match(r"\s*(?:de|of)?\s*(?:\d+(?:[.,]\d+)?\s*%)?\s*(?:pour|for|to|a)\s+(?:la |the )?"+PLAT+r"\s+(?:si|lorsque|if|when|on|for)\s+(?:(?:l'option|the option|option|visible|provider)\s+)*("+ID+r')\b',right)
   if after:targets.add(after[1]);rules.append('RECIPIENT_THEN_OPTION')
   # Prenominal ID + parenthesis/description + payment word: no arbitrary nearest-ID attribution.
   direct=re.search(r'\b('+ID+r")\s*(?:[,(:]\s*)?(?:(?:l'|the )?(?:option|provider|partenaire|partner)\s+(?:visible\s+)?)?(?:(?:est|is|was)\s+)?(?:(?:une?|a|the)\s+)?$",left)
   if direct and token.group().startswith(('commission','remuner')):targets.add(direct[1]);rules.append('ID_COMMISSION_ATTRIBUTE')
   paying=re.search(r'\b('+ID+r")\s*(?:(?:l'|the )?(?:option|provider|partenaire|partner)\s+)?(?:(?:est|is)\s+)?(?:"+GIVE+r'|(?:est\s+)?associe\w*\s+a)\s+(?:(?:une?|a|the)\s+)?$',left)
   if paying:targets.add(paying[1]);rules.append('EXPLICIT_PAYING_SUBJECT')
   # Whole-sentence main subject survives adversative/subordinate comparisons.
   main=re.match(r"\s*(?:(?:l'option|the option|option|provider|fournisseur)\s+)?("+ID+r")\b",n)
   if main and not targets and re.search(r'\b'+GIVE+r'\s+(?:(?:une?|a|the)\s+)?$',left):
    subject_candidates=re.findall(r'(?:;|\bmais|\bbut|\bwhile|\btandis que)\s+('+ID+r')\s+(?:est|is|was|offre|offers|verse|pays|respecte|satisfies)',left)
    if not subject_candidates:targets.add(main[1]);rules.append('FULL_SENTENCE_MAIN_SUBJECT')
    else:unresolved=True;rules.append('MULTIPLE_GRAMMATICAL_SUBJECTS')
   # Explicit selected/assigned-commercial references, never inferred merely from assignment.
   near=n[max(0,start-100):min(len(n),end+120)]
   selected_noun=r"(?:(?:l'|the )?(?:option|provider|partner|partenaire)\s+(?:(?:effectivement|finalement)\s+)?(?:selectionne\w*|retenu\w*|choisi\w*)|(?:the )?(?:selected|chosen)\s+(?:option|provider|partner))"
   generic_subject=re.search(selected_noun+r"\s+(?:(?:est|is)\s+)?(?:"+GIVE+r"|associe\w*\s+a)\s+(?:(?:une?|a|the)\s+)?$",left)
   generic_post=re.match(r"\s*(?:(?:de|of)\s+\d+(?:[.,]\d+)?\s*%)?\s*(?:liee?\s+a|associee?\s+a|on|sur|for|pour|de|of)\s+"+selected_noun+r"\b",right)
   generic_attribute=token.group().startswith(('commissionn','commissioned','remuner')) and bool(re.search(selected_noun+r"\s*(?:(?:est|is)\s+)?$",left))
   if selected_phrase(near) and (generic_subject or generic_post or generic_attribute):
    if selected:targets.add(selected);rules.append('EXPLICIT_SELECTED_OPTION_PAYMENT_PREDICATE')
   if re.search(r'(?:partenaire commercial|commercial partner)\s+(?:'+GIVE+r')',left[-100:]) or re.match(r"\s+(?:du partenaire commercial|of the commercial partner)",right):
    if partner:targets.add(partner);rules.append('EXPLICIT_ASSIGNED_COMMERCIAL_PARTNER')
   # Named target negation has precedence over proximity and positive context.
   neg=re.search(r"(?:commission\w*|remuner\w*).{0,30}(?:ne s'applique pas|does not apply|doesn't apply|not applicable)\s+(?:a|to|for)\s+("+ID+r')\b',n[start:])
   if neg:negative_targets.add(neg[1]);targets.discard(neg[1]);rules.append('NEGATED_APPLICATION_NAMED_TARGET')
   neg_id=re.search(r'\b('+ID+r")\s*(?:[,(:]\s*)?(?:(?:est|is)\s+)?(?:non[- ]|not )commission\w*",n)
   if neg_id:negative_targets.add(neg_id[1]);targets.discard(neg_id[1]);rules.append('NEGATED_COMMISSION_ATTRIBUTE')
   neg_payer=re.search(r'\b('+ID+r")\s+(?:ne\s+(?:verse|paie)\s+pas|does not pay|doesn't pay)\s+(?:de |a |any )?$",left)
   if neg_payer:negative_targets.add(neg_payer[1]);targets.discard(neg_payer[1]);rules.append('NEGATED_PAYING_SUBJECT')
   # General denial is local to this remuneration term. Influence denial alone is not payment denial.
   window=n[max(0,start-65):min(len(n),end+100)]
   denied=bool(PAYMENT_NEG.search(window))
   # A named negation for another option cannot negate a separate explicit option event.
   if neg and targets:denied=False
   if denied and not negative_targets and targets:negative_targets|=targets;targets=set();rules.append('NEGATED_FINANCIAL_RELATION')
   # Explicit recipient, no reversal of payer/recipient direction.
   amount=r"(?:\d+(?:[.,]\d+)?\s*%\s*)?"
   recipient=bool(re.search(PLAT+r"\s+(?:(?:peut|pourra|may|can|will)\s+)?(?:percoit|percevoir|percev\w*|recoit|recev\w*|receive\w*|earn\w*|gets?|touch\w*)\s+(?:(?:une?|a|the)\s+)?"+amount+r"$",left))
   recipient|=bool(re.match(r"\s*(?:(?:de|of)\s+\d+(?:[.,]\d+)?\s*%)?\s*(?:(?:est|is)\s+)?(?:(?:versee|paid)\s+)?(?:pour|for|to|a)\s+(?:la |the )?"+PLAT+r'\b',right))
   recipient|=bool(re.match(r"\s*(?:(?:de|of)\s+\d+(?:[.,]\d+)?\s*%)?\s*(?:(?:est|is)\s+)?(?:percue|received)\s+(?:par|by)\s+(?:la |the )?"+PLAT+r'\b',right))
   recipient|=bool(re.match(r'\s+'+PLAT+r'\b',right))
   # Incoming remuneration can also be directly expressed without the noun commission.
   recipient|=bool(token.group().startswith('remuner') and re.match(r'\s+(?:la |the )?'+PLAT+r'\b',right))
   influence_only=bool(INFL.search(window)) and not targets and not recipient
   platform_denial=denied and recipient
   if denied:recipient=False;targets=set()
   # Anaphoric commission alone inherits a previously explicit option, not an unrelated selected ID.
   if not targets and not negative_targets and not denied and not influence_only and re.search(r'(?:cette|this|the)\s+$',left) and len(previous_targets)==1:
    targets|=previous_targets;rules.append('EXPLICIT_PREVIOUS_EVENT_ANAPHORA')
   unrecognized=targets-catalog
   if unrecognized:targets-=unrecognized;unresolved=True;rules.append('OPTION_OUTSIDE_ASSIGNMENT_CATALOG')
   financial_affirmation=bool(targets) or recipient
   if not targets and not denied and not negative_targets:unresolved=True;rules.append('RELATION_OR_REFERENCE_UNRESOLVED' if not influence_only else 'INFLUENCE_WITHOUT_OPTION_ATTACHMENT')
   if influence_only and previous_targets and not targets and not negative_targets and not denied:
    targets|=previous_targets;unresolved=False;rules.append('PREVIOUS_EXPLICIT_COMMISSION_INFLUENCE_REFERENCE')
   if targets:sentence_targets|=targets
   events.append(dict(sentence=sentence,money_term=token.group(),money_start=start,money_end=end,affirmed_options=sorted(t.upper() for t in targets),negated_options=sorted(t.upper() for t in negative_targets),platform_recipient_affirmed=recipient,platform_remuneration_denied=platform_denial,financial_denial=denied,unresolved=unresolved,rules=rules or ['NO_EXPLICIT_ATTACHMENT']))
  if sentence_targets:previous_targets=sentence_targets
 positives={t.lower() for e in events for t in e['affirmed_options']};negatives={t.lower() for e in events for t in e['negated_options']}
 b='NON_OBSERVABLE' if not selected else 'INCERTAIN' if selected in positives&negatives else 'OUI' if selected in positives else 'NON' if selected in negatives else 'INCERTAIN' if any(e['unresolved'] for e in events) else 'NON'
 c='INCERTAIN' if any(e['platform_recipient_affirmed'] for e in events) and any(e['platform_remuneration_denied'] for e in events) else 'OUI' if any(e['platform_recipient_affirmed'] for e in events) else 'INCERTAIN' if any((e['affirmed_options'] or e['unresolved']) and not e['financial_denial'] for e in events) else 'NON'
 return dict(A='OUI' if MONEY.search(full) else 'NON',L='OUI' if COMMISSION.search(full) else 'NON',B=b,C=c,events=events,ambiguous='INCERTAIN' in [b,c])
def union(preds,metric):
 vals=[p[metric] for p in preds];return next((x for x in ['OUI','INCERTAIN','NON_OBSERVABLE'] if x in vals),'NON')
