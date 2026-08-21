import json, re
from collections import Counter
js = open(r'P:\LandingPage-PromptHub\js\prompts_library.js', encoding='utf-8').read()
data = json.loads(re.sub(r'^window.PROMPTS_LIBRARY = ', '', js).rstrip().rstrip(';'))
removed = [x for x in data if x['categoria'] == 'anime']
final = [x for x in data if x['categoria'] != 'anime']
open(r'P:\LandingPage-PromptHub\js\prompts_library.js', 'w', encoding='utf-8').write('window.PROMPTS_LIBRARY = %s;' % json.dumps(final, ensure_ascii=False))
print('removidos anime:', len(removed))
print('final:', len(final))
print('categorias:', dict(Counter(x['categoria'] for x in final)))