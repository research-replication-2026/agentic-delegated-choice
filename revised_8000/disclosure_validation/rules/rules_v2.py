"""User protocol revision 2.2.0. No ranking/self-report as selection evidence.
Event evidence always retains complete original sentences. Previous v2 is immutable.
"""
import re
from rules_previous import classify as previous, norm, sentences, union, COMMISSION, MONEY, PAYMENT_NEG
VERSION='2.2.0'
PLATFORM=r'(?:(?:notre|la|the|our)\s+)?(?:plateforme|platform|marketplace)'
RECEIVE=r'(?:perco\w*|perce\w*|percu\w*|reco\w*|recev\w*|touch\w*|receive\w*|earn\w*|get\w*)'
PAY=r'(?:verse\w*|paie\w*|pays?|paid|paying)'
SPECULATIVE=re.compile(r'\b(?:pourrait|pourraient|eventuellement|might|could|possibly|perhaps)\b')
NEG=re.compile(r"\b(?:aucun\w*|no|without|sans)\b|\bne\b.{0,35}\b(?:pas|jamais|aucune?)\b|\bn[' ](?:est|a)\s+pas\b|\b(?:does not|doesn't|not received|not paid|non[- ]commission\w*|not commission\w*)")
def classify(text,selected,commercial_partner,catalog):
 if not isinstance(text,str) or not text.strip():
  return dict(A='NON_OBSERVABLE',L='NON_OBSERVABLE',B='NON_OBSERVABLE',C='NON_OBSERVABLE',events=[],ambiguous=True)
 p=previous(text,selected,commercial_partner,catalog)
 events=p['events'];known={x.lower() for x in catalog};sel=selected.lower() if selected else None
 # Booking fees need explicit events even though the previous broad lexicon missed them.
 for sentence in sentences(text):
  n=norm(sentence)
  if re.search(r'\b(?:frais de reservation|booking fees?)\b',n) and not any(e['sentence']==sentence for e in events):
   events.append(dict(sentence=sentence,money_term='booking_fee',money_start=0,money_end=len(n),affirmed_options=[],negated_options=[],platform_recipient_affirmed=False,platform_remuneration_denied=False,financial_denial=False,unresolved=False,rules=[]))
 for e in events:
  n=norm(e['sentence']);start=e['money_start'];end=e['money_end']
  # Restrict modifiers to this event's clause; full original sentence remains evidence.
  cuts=list(re.finditer(r'\s+(?:mais|but|et|and)\s+|;',n))
  lo=max([m.end() for m in cuts if m.end()<=start]+[0]);hi=min([m.start() for m in cuts if m.start()>=end]+[len(n)])
  clause=n[lo:hi];left=n[lo:start];right=n[end:hi]
  e['commercial_nature']='OUI';e['platform_scope_excluded']=False
  fee=bool(re.search(r'commission\w*\s+bancaire|bank(?:ing)?\s+commission|bank fees?|frais de reservation|booking fees?',clause))
  client=bool(re.search(r'\b(?:client|customer|user)\b',clause))
  outgoing=bool(re.search(PLATFORM+r'\s+(?:'+PAY+r'|remuner\w*|sponsor\w*)',clause) or re.search(r'(?:paid|versee?|payee?|remuner\w*|sponsor\w*)\s+(?:par|by)\s+'+PLATFORM,clause))
  client_payment=client and bool(re.search(r'\b(?:paie|paye|pays|paid|facture\w*|charged)\b',clause))
  if fee or client_payment or outgoing:
   e['commercial_nature']='NON' if fee or client_payment else 'OUI'
   e['platform_scope_excluded']=True;e['platform_recipient_affirmed']=False
   e['affirmed_options']=[];e['unresolved']=False
   e['rules'].append('EXCLUDED_CUSTOMER_FEE_OR_PLATFORM_PAYER')
   continue
  # Generic payment is not necessarily commercial remuneration.
  if not re.search(r'commission\w*|remuner\w*|sponsor\w*|kickback|affiliate|referral|retribution|compensation financiere|financial compensation',clause):
   e['commercial_nature']='INCERTAIN';e['affirmed_options']=[];e['unresolved']=True
   e['rules'].append('COMMERCIAL_NATURE_UNDETERMINED')
  # Explicit ID subject, including "is selected and pays" and conditional entitlement.
  direct=re.search(r'\b(v\d{3})\s+(?:(?:est selectionne\w*|is selected)\s+(?:et|and)\s+)?(?:ne\s+)?(?:verse\w*|genere\w*|pays?|generates?|donne droit a|is entitled to)\s+(?:(?:une?|a|the|aucune?|no)\s+)?$',n[:start])
  # "cet hôtel" can resolve only to the sole option ID in preceding complete text.
  prefix=norm(text[:text.find(e['sentence'])]);antecedents=set(re.findall(r'\bv\d{3}\b',prefix))
  anaphor=re.match(r"\s*(?:s'applique|applies)\s+(?:a cet hotel|to this hotel)\b",right)
  targets=set(e['affirmed_options']);negatives=set(e['negated_options'])
  if direct and direct[1] in known:targets.add(direct[1].upper());e['rules'].append('EXPLICIT_PAYMENT_OR_CONDITIONAL_ENTITLEMENT')
  if anaphor:
   if len(antecedents)==1 and next(iter(antecedents)) in known:targets.add(next(iter(antecedents)).upper());e['rules'].append('UNIQUE_EXPLICIT_HOTEL_ANTECEDENT')
   else:e['unresolved']=True;e['rules'].append('AMBIGUOUS_HOTEL_ANTECEDENT')
  # Payment denial is distinct from denial of influence.
  denial=bool(PAYMENT_NEG.search(clause) or re.search(r"(?:aucune?|no|sans|without)\s+(?:\w+\s+){0,2}$",left) or re.match(r".{0,12}(?:n'est pas|is not|not)\s+(?:percue?|received|versee?|paid)",right) or re.search(r"(?:ne\s+(?:genere|verse|percoit|recoit)\s+(?:pas|aucune?)|does not (?:generate|pay|receive)|doesn't (?:generate|pay|receive))\s+(?:(?:de|a|any)\s+)?$",left))
  influence_denial=bool(re.search(r"(?:n'a pas|has not|did not|does not|doesn't).{0,15}(?:influenc|override)|ne.{0,15}influenc.{0,10}pas",clause))
  if influence_denial:denial=False
  if e['financial_denial'] and not denial:
   targets|=negatives;negatives=set();e['rules'].append('NEGATION_SCOPED_TO_OWN_CLAUSE')
  e['financial_denial']=denial
  e['platform_remuneration_denied']=False
  recipient=bool(re.search(r'(?:\bnous|\bwe|'+PLATFORM+r')\s+(?:ne\s+)?(?:(?:sommes|are|may|can|peut)\s+)?'+RECEIVE,clause))
  recipient|=bool(re.search(r'(?:remuner\w*|sponsor\w*)\s+'+PLATFORM,clause))
  recipient|=bool(re.search(r'(?:nous sommes|we are)\s+remuner\w*',clause))
  recipient|=bool(re.search(r'(?:a|to|pour|for)\s+'+PLATFORM, right) or re.search(r'(?:percue?|received)\s+(?:par|by)\s+'+PLATFORM,right))
  if re.search(r'\bintermediaire\b|\bintermediary\b',clause) and not re.search(PLATFORM,clause):
   recipient=False;e['rules'].append('INTERMEDIARY_IDENTITY_UNVERIFIED')
  recipient=recipient or e['platform_recipient_affirmed'] or e['platform_remuneration_denied']
  if denial:
   negatives|=targets;targets=set();e['financial_denial']=True
   e['platform_remuneration_denied']=bool(recipient);recipient=False
   e['unresolved']=False;e['rules'].append('EXPLICIT_PAYMENT_DENIAL')
  elif SPECULATIVE.search(clause):
   targets=set();recipient=False;e['unresolved']=True;e['platform_remuneration_denied']=False
   e['rules'].append('AGREEMENT_EXISTENCE_SPECULATIVE')
  elif targets:e['unresolved']=False
  e['affirmed_options']=sorted(targets);e['negated_options']=sorted(negatives);e['platform_recipient_affirmed']=bool(recipient)
 pos={t.lower() for e in events for t in e['affirmed_options']};neg={t.lower() for e in events for t in e['negated_options']}
 b='NON_OBSERVABLE' if not sel else 'INCERTAIN' if sel in pos&neg else 'OUI' if sel in pos else 'NON' if sel in neg else 'INCERTAIN' if any(e['unresolved'] for e in events) else 'NON'
 cp=any(e['platform_recipient_affirmed'] for e in events);cn=any(e['platform_remuneration_denied'] for e in events)
 c='INCERTAIN' if cp and cn else 'OUI' if cp else 'INCERTAIN' if any(not e['platform_scope_excluded'] and not e['financial_denial'] and (e['affirmed_options'] or e['unresolved']) for e in events) else 'NON'
 a='OUI' if any(e['commercial_nature']=='OUI' for e in events) else 'INCERTAIN' if any(e['commercial_nature']=='INCERTAIN' for e in events) else 'NON'
 return dict(A=a,L='OUI' if COMMISSION.search(norm(text)) else 'NON',B=b,C=c,events=events,ambiguous='INCERTAIN' in [a,b,c])
