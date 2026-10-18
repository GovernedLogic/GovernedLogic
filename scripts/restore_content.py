"""One-time mechanical recovery; authored passages remain in their source editions."""
from pathlib import Path
import subprocess, re, json, html, hashlib
ROOT = Path(__file__).resolve().parents[1]
def git(ref, path):
    return subprocess.check_output(['git','show',f'{ref}:{path}'],cwd=ROOT).decode('utf-8')
def write(path, value):
    target=ROOT/path; target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(value,encoding='utf-8',newline='\n')
def page(title, route, body, description, extra=''):
    data={'@context':'https://schema.org','@type':'WebPage','name':title,'url':'https://governedlogic.com'+route,'description':description,'isPartOf':{'@id':'https://governedlogic.com/#website'},'author':{'@id':'https://governedlogic.com/about/#paul'}}
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+' | Governed Logic Reasoning Systems</title><meta name="description" content="'+html.escape(description,quote=True)+'"><link rel="canonical" href="https://governedlogic.com'+route+'"><meta name="robots" content="index,follow"><link rel="stylesheet" href="/assets/restored-site.css"><script type="application/ld+json">'+json.dumps(data,ensure_ascii=False)+'</script>'+extra+'</head><body><!--SITE_HEADER--><main class="document-main" id="content"><article><p class="eyebrow">GOVERNED LOGIC REASONING SYSTEMS</p><h1>'+html.escape(title)+'</h1>'+body+'</article></main><!--SITE_FOOTER--></body></html>\n'

# Preserve the current native opening verbatim; replace only the content beneath it.
home=git('267d30bdce7eda45f18a79a619a67f96ead45570','index.html')
home=re.sub(r'<header class="site-bar">.*?</header>','<!--SITE_HEADER-->',home,flags=re.S)
home=re.sub(r'<main class="site-content".*?</main>',lambda m:(ROOT/'content/home.html').read_text(encoding='utf-8'),home,flags=re.S)
home=re.sub(r'<footer.*?</footer>','<!--SITE_FOOTER-->',home,flags=re.S)
home=home.replace('assets/site-navigation.css','/assets/restored-site.css')
home=home.replace('content="Governed Logic Reasoning Systems."','content="Governed Logic Reasoning Systems is building Governed Intelligence, a reasoning engine and API. Explore the architecture, prototype, research, and source works."')
write('index.html',home)

recovered=[*sorted((ROOT/'concepts').rglob('index.html')),ROOT/'company/index.html',ROOT/'research/index.html',ROOT/'about/index.html',ROOT/'mechanism.html',ROOT/'sources/index.html']
provenance=[]
for path in recovered:
    source=path.read_text(encoding='utf-8')
    provenance.append({'path':path.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'revision':'origin/biography-presentation-pass' if path.parts[-2]=='about' else '9caacb3556ad0b583113aebad0f95028ad84c833'})
    source=re.sub(r'<header\b.*?</header>','<!--SITE_HEADER-->',source,flags=re.S)
    source=re.sub(r'<footer\b.*?</footer>','',source,flags=re.S)
    source=re.sub(r'<a class="skip-link".*?</a>','',source,flags=re.S)
    source=re.sub(r'<style>.*?</style>','',source,flags=re.S)
    source=re.sub(r'<link rel="stylesheet"[^>]*>','',source)
    source=source.replace('</head>','<meta name="robots" content="index,follow"><link rel="stylesheet" href="/assets/restored-site.css"></head>')
    source=source.replace('</body>','<!--SITE_FOOTER--></body>')
    if '<!--SITE_HEADER-->' not in source: source=source.replace('<body>','<body><!--SITE_HEADER-->')
    source=re.sub(r'<main(?: class="[^"]*")?>','<main class="document-main" id="content">',source)
    source=source.replace('https://governedlogic.com/#paul','https://governedlogic.com/about/#paul')
    source=source.replace('Follow the Chain Challenge','Follow the chain.').replace('Follow the Chain','Follow the chain.')
    # Remove implementation instructions from public company prose, preserving authored explanations.
    if path.parts[-2]=='company':
        source=re.sub(r'<section id="novelty".*?</section>','',source,flags=re.S)
        for text in ['Committed development direction','Planned engineering deliverable','New company identity — decided by Paul']:
            source=source.replace(text,'In development')
        for paragraph in ['They should not all be grouped under the generic label of content marketing.', 'Paul will provide or confirm the final name of the publishing division or imprint. Until then, do not invent a new branded name.']:
            source=source.replace('<p>'+paragraph+'</p>','')
    if path.parts[-2]=='ultimate-grounding':
        source=source.replace('<h1>Ultimate grounding</h1>','<h1>On the Nature of Ultimate Grounding</h1>')
        source=source.replace('<blockquote>Why anything?</blockquote>','<a class="source-edition" href="/sources/01_Ultimate_Grounding_2026-09-22_172847_EDT.pdf">Read the complete treatise · PDF · 22 September 2026 →</a><blockquote>Why anything?</blockquote>')
    write(path.relative_to(ROOT),source)
write('recovery-provenance.json',json.dumps(provenance,indent=2))

# The inquiry uses Paul's verbatim October 18 assignment, not invented challenge rules.
inquiry='<p class="lede">The objective is truth, not winning an argument.</p><p>Investigate whether propositions, premises, inferences, and conclusions correspond to reality.</p><p>Examine the reasoning chain from premise through inference, adjudication, conclusion, representation, and termination.</p><section class="business-section"><h2>Representations are answerable to their referents.</h2><p>The referent remains the referent regardless of the representations used to reason about it.</p><p>A representation of a state is not the state it represents.</p><p>Changing a representation does not change the represented state.</p></section><section class="business-section"><h2>Truth governs logic.</h2><p>Logic governs reasoning.</p><p>Reasoning is upstream of intelligence.</p><div class="reading-links"><a href="/concepts/governed-logic/">The reasoning architecture →</a><a href="/concepts/ultimate-grounding/">The grounding argument →</a><a href="/research/">The research method →</a></div></section>'
write('challenge/index.html',page('Follow the chain.','/challenge/',inquiry,'The objective is truth, not winning an argument.'))
write('challenge/index.json',json.dumps({'title':'Follow the chain.','canonical_url':'https://governedlogic.com/challenge/','purpose':'The objective is truth, not winning an argument.','method':['Investigate whether propositions, premises, inferences, and conclusions correspond to reality.','Examine the reasoning chain from premise through inference, adjudication, conclusion, representation, and termination.']},ensure_ascii=False,indent=2))

questions=[
('What is Governed Logic?','Governed Logic is the upstream, bidirectional reasoning architecture in which truth governs logic, logic governs reasoning, and reasoning remains answerable to its ultimate ground.','/concepts/governed-logic/'),
('What is Governed Intelligence?','Governed Intelligence is the artificial intelligence implementation of Governed Logic.','/concepts/governed-intelligence/'),
('What exists today?','The company already has a working instruction-level prototype, which serves as the starting point for further research, development, and engineering.','/mechanism.html'),
('Are the reasoning engine and API available?','The engine and API are planned engineering deliverables, not currently available production services.','/company/#reasoning-engine'),
('What does ultimate grounding mean?','An ultimate ground is not grounded by something more fundamental in the same relevant respect.','/concepts/ultimate-grounding/'),
('What can model experiments establish?','Model behavior can provide evidence about the effects, stability, and failure modes of an implementation. It cannot independently prove a metaphysical thesis, a historical claim, or the identity of the ultimate ground.','/research/#limits'),
('Who is behind Governed Logic?','Paul André Couchoud is the founder of Governed Logic Reasoning Systems and creator of Governed Logic.','/about/')]
faq=''.join('<details class="faq-item"><summary>'+q+'</summary><p>'+a+'</p><a href="'+u+'">Read more →</a></details>' for q,a,u in questions)
schema={'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a,u in questions]}
write('faq/index.html',page('Questions & answers','/faq/',faq,'Explore the architecture, the existing prototype, the research, and the work in development.','<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False)+'</script>'))
write('faq/index.json',json.dumps(schema,ensure_ascii=False,indent=2))

# Keep the two October 14 alternatives separate: publish one complete source edition,
# and the distinct integrity section, without blending the competing Why Anything texts.
why=git('0d8d53c0d5d8d19401a342b3471f825a761a6a48','index.html')
article=re.search(r'<article\b[^>]*>(.*?)</article>',why,re.S).group(1)
article=re.sub(r'<h[12][^>]*>Why Anything\?</h[12]>','',article,flags=re.I)
write('articles/why-anything/index.html',page('Why Anything?','/articles/why-anything/',article+'<p class="provenance">Paul André Couchoud · Source edition: 14 October 2026.</p>','Why does anything exist at all rather than nothing?'))
truth=git('d891268e99843bca2f16c9f7b2c17514872f3368','index.html')
integrity=truth.split('<h2>Integrity in Artificial Intelligence</h2>')[1].split('</section>')[0]
write('articles/integrity-in-artificial-intelligence/index.html',page('Integrity in Artificial Intelligence','/articles/integrity-in-artificial-intelligence/',integrity+'<p class="provenance">Paul André Couchoud · Source edition: 14 October 2026.</p>',"Artificial intelligence should tell people the truth, avoid pretending to be something it isn't, and not mislead them about reality."))
print('Recovered substantive pages and source editions.')
