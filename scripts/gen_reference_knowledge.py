from pathlib import Path

# Helper
def add_block(lines, header, items):
    lines.append(header)
    lines.extend(items)
    lines.append("")

# ASTROLOGY
ast = []
ast.append("ASTROLOGY_REFERENCE = \"\"\"")
ast.append("ASTROLOGY REFERENCE")
ast.append("Tone: grounded, symbolic, psychological. Use suggests/indicates/points toward.")
ast.append("")

sun_signs = [
    ("Aries","Fire","Cardinal","Mars","initiator","courage, immediacy, self-definition","directness with restraint","impulsivity and impatience","starting quickly, preferring action","values candor and momentum","thrives in launch phases","learning pause and follow-through"),
    ("Taurus","Earth","Fixed","Venus","builder","reliability, sensory wisdom, pacing","steady progress and mastery","stubbornness and inertia","deepens what already works","shows care through consistency","strong in maintenance roles","embracing flexibility"),
    ("Gemini","Air","Mutable","Mercury","messenger","curiosity, language, variety","adaptive intelligence and nuance","scattered focus","collecting ideas and translating","engages through dialogue","strong in research and media","committing to depth"),
    ("Cancer","Water","Cardinal","Moon","protector","belonging, memory, care","healthy boundaries and empathy","over-guarding and withdrawal","protecting what is vulnerable","offers loyalty and warmth","strong in caregiving","distinguishing care from control"),
    ("Leo","Fire","Fixed","Sun","creator","self-expression, pride, generosity","heart-led leadership","need for validation","seeks recognition and ownership","shows love through warmth","thrives in leadership and arts","sharing the spotlight"),
    ("Virgo","Earth","Mutable","Mercury","craftsperson","precision, service, discernment","practical healing and refinement","perfectionism and worry","optimizing systems and routines","shows care through attentiveness","excellent in diagnostics","accepting imperfection"),
    ("Libra","Air","Cardinal","Venus","mediator","balance, aesthetics, fairness","skilled diplomacy","avoidance of conflict","weighing perspectives","values reciprocity","strong in negotiation","choosing clarity"),
    ("Scorpio","Water","Fixed","Mars/Pluto","investigator","intensity, depth, truth-seeking","honest intimacy and resilience","control and secrecy","probing beneath surfaces","needs trust and loyalty","thrives in research","softening into vulnerability"),
    ("Sagittarius","Fire","Mutable","Jupiter","seeker","meaning, freedom, perspective","vision with humility","restlessness and bluntness","pursuing horizons","values openness and growth","strong in teaching","committing to the path"),
    ("Capricorn","Earth","Cardinal","Saturn","strategist","discipline, structure, responsibility","earned authority","rigidity and workaholism","carrying responsibility early","shows care through reliability","excels in management","allowing rest"),
    ("Aquarius","Air","Fixed","Saturn/Uranus","reformer","innovation, community, independence","originality for collective good","detachment and contrarianism","questioning norms","values autonomy and friendship","strong in technology","balancing intellect and feeling"),
    ("Pisces","Water","Mutable","Jupiter/Neptune","empath","compassion, imagination, surrender","empathy with boundaries","escapism and confusion","absorbing emotional tone","offers forgiveness","thrives in healing arts","clarity of limits"),
]

ast.append("SUN SIGNS")
for name, element, modality, ruler, arch, themes, integrated, imbalanced, patterns, relations, work, growth in sun_signs:
    ast += [
        f"Sun Sign: {name}",
        f"Element: {element}",
        f"Modality: {modality}",
        f"Ruling Planet: {ruler}",
        f"Core archetype suggests the {arch} pattern.",
        f"Core themes indicate {themes}.",
        f"Integrated expression points toward {integrated}.",
        f"Imbalanced expression suggests {imbalanced}.",
        f"Common life patterns indicate {patterns}.",
        f"Relational style suggests someone who {relations}.",
        f"Work style indicates a person who {work}.",
        f"Growth edge points toward {growth}.",
        "Sun sign indicates identity and vitality, not fixed fate.",
        "Use as a central anchor among other placements.",
        "",
    ]

moon_signs = [
    ("Aries","quick emotional ignition","movement and direct expression","impatient when slowed"),
    ("Taurus","steady emotional rhythm","comfort, routine, and touch","resists change when threatened"),
    ("Gemini","curious feelings","conversation and variety","overthinks when insecure"),
    ("Cancer","protective sensitivity","home, memory, and loyalty","withdraws when trust feels unsure"),
    ("Leo","warm-hearted pride","appreciation and creative play","reacts strongly to dismissal"),
    ("Virgo","practical care","useful roles and small acts","self-criticizes under pressure"),
    ("Libra","relational balance","harmony and fairness","avoids conflict to keep peace"),
    ("Scorpio","intense depth","truth and loyalty","guards vulnerability tightly"),
    ("Sagittarius","expansive outlook","meaning and freedom","deflects with humor"),
    ("Capricorn","contained style","competence and stability","fears appearing needy"),
    ("Aquarius","observational tone","space and perspective","detaches when overwhelmed"),
    ("Pisces","porous empathy","gentleness and imagination","absorbs others' moods"),
]

ast.append("MOON SIGNS")
for name, tone, soothe, stress in moon_signs:
    ast += [
        f"Moon Sign: {name}",
        f"Emotional tone suggests {tone}.",
        f"Soothing needs indicate {soothe}.",
        f"Under stress, this Moon points toward {stress}.",
        "Nurturing style suggests consistent presence.",
        "Attachment patterns indicate a need for reliability.",
        "Integration points toward naming feelings without rushing them.",
        "Moon sign reflects inner needs, not public persona.",
        "",
    ]

rising_signs = [
    ("Aries","direct, brisk first impressions","leads with action and candor"),
    ("Taurus","calm, grounded presence","moves deliberately and prefers tangible cues"),
    ("Gemini","curious, quick rapport","leads with questions and observation"),
    ("Cancer","soft, protective aura","leads with care and attunement"),
    ("Leo","radiant, confident presence","leads with warmth and visibility"),
    ("Virgo","precise, observant demeanor","leads with helpfulness and detail"),
    ("Libra","polished, relational ease","leads with harmony and social calibration"),
    ("Scorpio","intense, focused gaze","leads with depth and privacy"),
    ("Sagittarius","open, optimistic vibe","leads with humor and big-picture talk"),
    ("Capricorn","composed, responsible tone","leads with structure and purpose"),
    ("Aquarius","independent, original aura","leads with ideas and perspective"),
    ("Pisces","gentle, dreamy presence","leads with empathy and imagination"),
]

ast.append("RISING SIGNS")
for name, impression, lead in rising_signs:
    ast += [
        f"Rising Sign: {name}",
        f"First impressions suggest {impression}.",
        f"Approach to new situations indicates someone who {lead}.",
        "Public style points toward learned social strategies.",
        "Integration suggests aligning outer style with inner needs.",
        "",
    ]

aspects = [
    ("Sun square Saturn","tension between vitality and duty","self-critique that matures into discipline","earned confidence"),
    ("Sun trine Jupiter","ease between identity and growth","optimism and generous leadership","opportunity through vision"),
    ("Sun opposite Moon","pull between aims and needs","need for integration","relational mirroring"),
    ("Moon trine Pluto","emotional depth with resilience","capacity to metabolize intensity","cathartic insight"),
    ("Moon square Neptune","sensitivity with blurred boundaries","strong imagination","discernment with feelings"),
    ("Mercury conjunct Saturn","structured thinking","careful speech and rigor","measured communication"),
    ("Mercury square Neptune","creative intuition with fog","poetic thinking","checking facts"),
    ("Venus conjunct Mars","magnetic attraction","direct desire","balance of charm and heat"),
    ("Venus opposite Saturn","testing of affection","fear of rejection","stable bonds over time"),
    ("Mars square Uranus","restless drive","sudden action","channeling risk into innovation"),
    ("Jupiter conjunct Saturn","expansion with realism","strategic growth","responsible optimism"),
    ("Jupiter trine Pluto","deepening influence","transformational faith","purposeful ambition"),
    ("Saturn opposite Uranus","tradition versus change","reform pressure","balanced innovation"),
    ("Saturn square Neptune","reality versus ideal","disillusionment cycles","grounding dreams"),
    ("Moon trine Venus","emotional grace","easy affection","soothing relationships"),
]

ast.append("MAJOR ASPECTS")
for name, a, b, c in aspects:
    ast += [
        f"Aspect: {name}",
        f"This aspect suggests {a}.",
        f"It indicates {b} when integrated.",
        f"It points toward {c} as a growth path.",
        "Aspects describe dynamics, not fixed outcomes.",
        "",
    ]

ast.append("ELEMENTS")
for name, a, b, c in [
    ("Fire","action, vitality, courage","enthusiasm and initiation","confidence through experience"),
    ("Earth","stability, material reality, stewardship","patience and practical skill","trust built over time"),
    ("Air","thought, language, connection","curiosity and social intelligence","meaning through dialogue"),
    ("Water","emotion, memory, intuition","empathy and depth","healing through feeling"),
]:
    ast += [
        f"Element: {name}",
        f"Core meaning suggests {a}.",
        f"Balanced expression indicates {b}.",
        f"Growth points toward {c}.",
        "Element describes how energy is processed.",
        "",
    ]

ast.append("MODALITIES")
for name, a, b, c in [
    ("Cardinal","initiation and leadership","tendency to begin and steer","learning follow-through"),
    ("Fixed","stability and persistence","loyalty and staying power","flexibility when needed"),
    ("Mutable","adaptation and synthesis","responsiveness and learning","committing to a direction"),
]:
    ast += [
        f"Modality: {name}",
        f"Core meaning suggests {a}.",
        f"Balanced expression indicates {b}.",
        f"Growth points toward {c}.",
        "Modality describes how energy moves.",
        "",
    ]

ast.append("\"\"\"")

# TAROT
tr = []
tr.append("TAROT_REFERENCE = \"\"\"")
tr.append("TAROT REFERENCE")
tr.append("Tone: grounded, symbolic, psychological. Use suggests/indicates/points toward.")
tr.append("")

major = [
    ("The Fool","beginnings, openness, trust","leap of faith","threshold requiring courage","curiosity without naivete","avoidance of responsibility","traveler at the cliff"),
    ("The Magician","focus, skill, will","concentrated effort","tools are available","disciplined intention","manipulation or over-control","mastery of elements"),
    ("The High Priestess","intuition, inner knowing","quiet listening","answers grow in stillness","patience and reflection","withholding as defense","veils and hidden knowledge"),
    ("The Empress","fertility, abundance, care","nurturing choices","growth through receptivity","tending what is alive","overindulgence or smothering","nature and creation"),
    ("The Emperor","structure, authority, order","need for boundaries","leadership and responsibility","building a stable foundation","rigidity or dominance","throne and law"),
    ("The Hierophant","tradition, learning, ethics","inherited values","mentorship or formal guidance","meaningful structure","conformity without understanding","ritual and lineage"),
    ("The Lovers","choice, alignment, union","defining decision","values need alignment","honest commitment","divided loyalties","moral choice"),
    ("The Chariot","direction, will, momentum","overcoming opposition","progress through focus","steering with discipline","pushing without integration","harnessed power"),
    ("Strength","courage, compassion, inner power","steady resilience","strength through gentleness","patience with instinct","pride or suppressed anger","lion and calm"),
    ("The Hermit","solitude, insight, discernment","retreat for clarity","need for reflection","inner guidance","isolation or avoidance","lantern and path"),
    ("Wheel of Fortune","cycles, change, timing","turning point","shifting conditions","adapting to cycles","feeling powerless","fate and rhythm"),
    ("Justice","balance, truth, consequence","reckoning","decisions need fairness","honest evaluation","harsh judgment","scales and sword"),
    ("The Hanged Man","pause, reversal, surrender","sacrifice reframed","need to let go","new perspective","stagnation or martyrdom","suspension"),
    ("Death","endings, transformation","chapter closed","necessary release","renewal through letting go","clinging to what is over","reaper"),
    ("Temperance","integration, moderation","blending opposites","steady healing","balance and patience","imbalance or excess","mixing and flow"),
    ("The Devil","bondage, desire, shadow","attachment formed","need to see the chain","honest accountability","denial of dependency","temptation"),
    ("The Tower","shock, disruption, truth","sudden rupture","unstable structures","clearing what is false","fear-driven resistance","lightning and collapse"),
    ("The Star","hope, renewal, clarity","recovery after strain","quiet optimism","trust in gradual healing","passive waiting","water and light"),
    ("The Moon","ambiguity, intuition, subconscious","uncertainty colored choices","mixed signals","careful discernment","confusion or projection","path at night"),
    ("The Sun","vitality, openness, success","moment of clarity","honest joy","directness and warmth","overexposure or ego","light and child"),
    ("Judgement","reckoning, awakening, renewal","call to responsibility","truth being faced","forgiveness and change","self-condemnation","trumpet"),
    ("The World","completion, integration, wholeness","lessons integrated","cycle closing","honoring completion","fear of ending","wreath"),
]

tr.append("MAJOR ARCANA")
for name, core, past, present, guidance, shadow, trad in major:
    tr += [
        f"Major Arcana: {name}",
        f"Core symbolism suggests {core}.",
        f"Past position indicates: {past}.",
        f"Present position indicates: {present}.",
        f"Guidance position points toward: {guidance}.",
        f"Shadow expression suggests: {shadow}.",
        f"Traditional note: {trad}.",
        "",
    ]

tr.append("SUIT THEMES AND ELEMENTS")
suit_data = [
    ("Wands","Fire","will, action, initiative, creativity","energy, drive, courage"),
    ("Cups","Water","feelings, relationships, empathy","emotional depth and bonding"),
    ("Swords","Air","thought, conflict, truth","clarity, decisions, tension"),
    ("Pentacles","Earth","material life, work, body","stability, craft, security"),
]
for name, element, themes, emphasis in suit_data:
    tr += [
        f"Suit: {name}",
        f"Elemental association: {element}.",
        f"Core themes suggest {themes}.",
        f"Balanced expression indicates {emphasis}.",
        "Shadow expression points toward stagnation or excess.",
        "Suit context shapes each card meaning.",
        "",
    ]

tr.append("NUMBER MEANINGS")
number_data = [
    ("Ace","origin and potential","fresh seed","initiative"),
    ("Two","choice and polarity","balance and negotiation","relationship"),
    ("Three","growth and collaboration","expansion","momentum"),
    ("Four","structure and stability","consolidation","boundaries"),
    ("Five","challenge and friction","testing","adaptation"),
    ("Six","harmony and repair","recalibration","learning"),
    ("Seven","assessment and complexity","mixed outcomes","strategy"),
    ("Eight","mastery and movement","sustained effort","discipline"),
    ("Nine","culmination and intensity","nearing completion","integration"),
    ("Ten","completion and outcome","cycle closing","transition"),
]
for name, a, b, c in number_data:
    tr += [
        f"Number: {name}",
        f"Core meaning suggests {a}.",
        f"In context, it indicates {b}.",
        f"Growth edge points toward {c}.",
        "Number meaning blends with suit meaning.",
        "",
    ]

tr.append("COURT CARD ROLES")
court_roles = [
    ("Page","learner and messenger","curiosity and a beginner's mindset"),
    ("Knight","mover and challenger","action, pursuit, testing courage"),
    ("Queen","holder and stabilizer","maturity, inner authority, care"),
    ("King","director and organizer","leadership, decision, responsibility"),
]
for name, role, nuance in court_roles:
    tr += [
        f"Court: {name}",
        f"Role suggests the {role} archetype.",
        f"It indicates {nuance}.",
        "Shadow expression points toward rigidity or immaturity.",
        "Court cards can indicate people, roles, or inner parts.",
        "",
    ]

tr.append("MINOR ARCANA")

suit_meaning = {
    "Wands": "initiative, creative drive, and will",
    "Cups": "emotional life, bonding, and receptivity",
    "Swords": "analysis, conflict, and truth-seeking",
    "Pentacles": "resources, work, and material stability",
}
number_lines = {
    "Ace": "a seed of potential that suggests beginnings",
    "Two": "a polarity that indicates choice or partnership",
    "Three": "a phase of growth that points toward collaboration",
    "Four": "a stabilizing pause that suggests structure",
    "Five": "a stress point that indicates friction or challenge",
    "Six": "a moment of repair that suggests recalibration",
    "Seven": "a complex stage that indicates strategy and assessment",
    "Eight": "a phase of movement that suggests mastery through effort",
    "Nine": "a peak that indicates intensity and integration",
    "Ten": "a completion that suggests transition to a new cycle",
}

for suit in ["Wands", "Cups", "Swords", "Pentacles"]:
    for num in ["Ace","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten"]:
        tr += [
            f"Minor Arcana: {num} of {suit}",
            f"This card suggests {number_lines[num]} within the domain of {suit_meaning[suit]}.",
            "Balanced expression indicates practical engagement with this theme.",
            "Shadow expression points toward excess, avoidance, or distortion.",
            "",
        ]

for suit in ["Wands", "Cups", "Swords", "Pentacles"]:
    for court, role, nuance in court_roles:
        tr += [
            f"Minor Arcana: {court} of {suit}",
            f"This court suggests the {role} within {suit_meaning[suit]}.",
            f"It indicates {nuance} expressed through {suit}.",
            "Shadow expression points toward overacting or withholding this role.",
            "",
        ]

tr.append("COMMON CARD COMBINATIONS")
combos = [
    ("The Hermit + Justice", "withdrawal to evaluate truth and consequences"),
    ("The Tower + The Star", "disruption followed by renewal"),
    ("The Lovers + Two of Cups", "alignment and mutual choice"),
    ("Death + Ten of Pentacles", "an ending that reshapes legacy"),
    ("Strength + Eight of Swords", "courage within mental constraint"),
    ("The Moon + Seven of Cups", "confusion that requires discernment"),
    ("The Sun + Six of Wands", "confidence and visible progress"),
    ("The Devil + Five of Pentacles", "attachment and scarcity thinking"),
    ("Temperance + Two of Swords", "balance needed before a decision"),
    ("The Chariot + Three of Wands", "momentum and expanding horizons"),
    ("The Magician + Ace of Wands", "initiative and focused skill"),
    ("The High Priestess + Four of Cups", "inner listening and emotional pause"),
    ("The Empress + Nine of Pentacles", "self-sufficiency and care"),
    ("The Emperor + Four of Pentacles", "control and boundary-setting"),
    ("Wheel of Fortune + Eight of Cups", "a change that invites departure"),
    ("Justice + King of Swords", "clear judgment and accountability"),
    ("The Hanged Man + Six of Cups", "reframing the past"),
    ("Judgement + Three of Pentacles", "a call to collaboration"),
    ("The World + Ten of Cups", "completion and emotional fulfillment"),
    ("The Star + Page of Cups", "renewal through openness"),
    ("The Fool + Eight of Wands", "quick movement and a leap forward"),
    ("The Hierophant + Five of Swords", "tension between rules and conflict"),
    ("The Devil + The Lovers", "attachment patterns in intimacy"),
    ("The Tower + Five of Wands", "conflict triggering restructure"),
    ("The Moon + The Hermit", "solitude to sort ambiguity"),
    ("The Sun + Queen of Wands", "confidence through leadership"),
    ("Death + The Fool", "reset and fresh beginning"),
    ("Temperance + Queen of Cups", "emotional regulation"),
    ("Strength + King of Pentacles", "steady courage and authority"),
    ("The Chariot + Knight of Swords", "fast movement needing control"),
    ("The Magician + Eight of Pentacles", "mastery through practice"),
    ("The High Priestess + The Moon", "intuition with uncertainty"),
    ("The Empress + Three of Cups", "nourishment through community"),
    ("The Emperor + Ten of Wands", "burdens tied to responsibility"),
    ("Wheel of Fortune + Two of Pentacles", "adapting to shifting demands"),
    ("Justice + Eight of Cups", "a fair but difficult departure"),
    ("The Hanged Man + Seven of Pentacles", "patience and long-term view"),
    ("Judgement + Ace of Swords", "a clear call to truth"),
    ("The World + Four of Wands", "completion and celebration"),
    ("The Star + Six of Swords", "healing through transition"),
]
for a, b in combos:
    tr += [
        f"Combination: {a}",
        f"Meaning: {b}.",
        "",
    ]

tr.append("\"\"\"")

# PALMISTRY
pl = []
pl.append("PALMISTRY_REFERENCE = \"\"\"")
pl.append("PALMISTRY REFERENCE")
pl.append("Tone: grounded, symbolic, psychological. Use suggests/indicates/points toward.")
pl.append("")

pl.append("MAJOR LINES")
major_lines = [
    ("Life Line","vitality and relationship to energy","stamina patterns and pacing","grounding and instinct"),
    ("Head Line","thinking style and mental focus","strategy, logic, or imagination","how decisions are processed"),
    ("Heart Line","emotional expression and bonding","relational values","how feeling is communicated"),
    ("Fate Line","structure, calling, responsibility","relationship to duty","sense of direction"),
]
for name, a, b, c in major_lines:
    pl += [
        f"Line: {name}",
        f"Core meaning suggests {a}.",
        "Length and depth indicate intensity and consistency.",
        "Breaks or branches suggest shifts in focus or environment.",
        f"When clear, this line suggests {b}.",
        f"When faint or fragmented, this line indicates {c}.",
        "Integration points toward conscious pacing and self-awareness.",
        "Lines indicate tendencies, not certainty.",
        "",
    ]

pl.append("MOUNTS")
mounts = [
    ("Venus","affection, sensuality, warmth","capacity for closeness","comfort with intimacy"),
    ("Jupiter","ambition, confidence, leadership","desire to grow","healthy authority"),
    ("Saturn","discipline, responsibility, realism","endurance","sober judgment"),
    ("Apollo","creativity, pride, recognition","artistic vitality","authentic expression"),
    ("Mercury","communication, wit, adaptability","social agility","practical intelligence"),
    ("Luna","imagination, empathy, dream life","intuitive attunement","emotional perception"),
]
for name, a, b, c in mounts:
    pl += [
        f"Mount: {name}",
        f"Core meaning suggests {a}.",
        "Prominence indicates emphasis and visibility of this trait.",
        "Flatness suggests subdued expression or learned restraint.",
        f"Balanced development indicates {b}.",
        f"Integration points toward {c}.",
        "Mounts describe temperament, not fixed outcomes.",
        "",
    ]

pl.append("HAND SHAPES")
hand_shapes = [
    ("Earth","square palm, short fingers","practicality, groundedness","focus on tangible results"),
    ("Air","square palm, long fingers","analytical thinking, curiosity","mental processing and communication"),
    ("Fire","rectangular palm, short fingers","action orientation, boldness","drive and immediacy"),
    ("Water","rectangular palm, long fingers","sensitivity, imagination","emotional and intuitive emphasis"),
]
for name, shape, a, b in hand_shapes:
    pl += [
        f"Hand Shape: {name}",
        f"Physical traits indicate {shape}.",
        f"Core meaning suggests {a}.",
        f"Balanced expression points toward {b}.",
        "Shadow expression indicates imbalance or overcompensation.",
        "Integration suggests using strengths with awareness.",
        "",
    ]

pl.append("FEATURE COMBINATIONS")
combos_palm = [
    ("Deep Life Line + Strong Venus","robust vitality and warmth"),
    ("Straight Head Line + Strong Saturn","pragmatic, disciplined thinking"),
    ("Curved Head Line + Luna Mount","imaginative and intuitive processing"),
    ("Chained Heart Line","emotional sensitivity and variability"),
    ("Broken Fate Line","shifts in responsibility or career direction"),
    ("Strong Jupiter + Long Fingers","ambition guided by planning"),
    ("Short Fingers + Fire Hand","decisive action and quick responses"),
    ("Long Fingers + Air Hand","mental agility and analysis"),
    ("Prominent Apollo + Clear Heart Line","expressive warmth"),
    ("Flat Venus + Straight Heart Line","restrained affection"),
    ("High Luna + Curved Head Line","vivid inner imagery"),
    ("Wide Palm + Strong Mercury","practical communication"),
]
for combo, meaning in combos_palm:
    pl += [
        f"Combination: {combo}",
        f"Meaning: {meaning}.",
        "Use as contextual clue, not a deterministic claim.",
        "",
    ]

pl.append("\"\"\"")

# VOICE
vc = []
vc.append("VOICE_LIBRARY = \"\"\"")
vc.append("VOICE LIBRARY")
vc.append("Tone: grounded, reflective, non-predictive. Use suggests/indicates/points toward.")
vc.append("")

vc.append("OPENING INVOCATIONS")
starters = [
    "We begin with what is true right now", "This reading starts with what your symbols indicate",
    "Consider this a map of meanings", "We will stay close to the signals your chart and cards suggest",
    "Let the symbols speak plainly", "This is an invitation to notice patterns already in motion",
    "We begin with grounded cues", "Think of this as a mirror for your present stance",
    "The aim here is clarity", "This reading favors honesty over certainty",
]
focus = [
    "before any story is layered on it.", "not what you are told to believe.", "rather than a set of outcomes.",
    "without forcing them into certainty.", "and allow meaning to build.", "and let them guide reflection.",
    "so we can be specific.", "as a structured reflection.", "not prediction.", "with care.",
]
opens = []
for s in starters:
    for f in focus:
        opens.append(f"{s}, {f}")
vc.extend(opens[:30])
vc.append("")

vc.append("CLOSING REFLECTION PROMPTS")
frames = [
    "What part of this reading", "Which symbol", "Where do you feel", "What would it mean",
    "How might you", "What is one choice", "Where might you", "What does", "What is the cost",
    "What is the simplest", "What needs to be", "What truth", "What boundary", "What habit",
]
topics = [
    "feels most grounded in your lived experience?", "pointed toward a truth you already sensed?",
    "asked to slow down and observe more closely?", "to act from clarity rather than urgency?",
    "test this insight gently rather than force it?", "aligns with your stated intention?",
    "be confusing intensity with clarity?", "a fair decision look like here?",
    "of staying where you are?", "next step that respects your energy?",
    "renegotiated rather than abandoned?", "are you avoiding because it feels uncomfortable?",
    "would support the pattern described here?", "supports the growth described here?",
]
closings = []
for f in frames:
    for t in topics:
        closings.append(f"{f} {t}")
vc.extend(closings[:50])
vc.append("")

vc.append("METAPHOR BANKS")
metaphors = {
    "responsibility": [
        "a load balanced across both shoulders",
        "a steady hand on the rudder",
        "a scaffolding that holds the next step",
        "a contract written in clear language",
        "a bridge that needs regular maintenance",
        "a calendar that protects priorities",
        "a foundation poured carefully",
        "a gate that opens with intention",
        "a compass set before the journey",
        "a boundary drawn with respect",
        "a promise you can actually keep",
        "a rhythm you return to each day",
    ],
    "love": [
        "a shared pace rather than a race",
        "a conversation that keeps returning to care",
        "a fire tended instead of chased",
        "a mirror that reflects without distortion",
        "a garden that needs seasons",
        "a door that opens slowly",
        "a bridge built from small acts",
        "a pact to tell the truth gently",
        "a place where repair is possible",
        "a practice of choosing again",
        "a holding that leaves room to breathe",
        "a steady light, not a flare",
    ],
    "transformation": [
        "a house renovated room by room",
        "a river changing course over time",
        "a skin shed after growth",
        "a threshold crossed with consent",
        "a seed breaking open",
        "a path cleared after a storm",
        "a lens cleaned to see clearly",
        "a routine rebuilt from scratch",
        "a tide that changes the shoreline",
        "a map updated after new terrain",
        "a knot loosened slowly",
        "a season turning without hurry",
    ],
}
for theme, items in metaphors.items():
    vc.append(f"Metaphors: {theme}")
    vc.extend(items)
    vc.append("")

vc.append("\"\"\"")

content = "\n".join(ast + [""] + tr + [""] + pl + [""] + vc) + "\n"
Path("backend/reference_knowledge.py").write_text(content, encoding="utf-8")

print("Wrote backend/reference_knowledge.py")
print("Total lines:", content.count("\n"))
