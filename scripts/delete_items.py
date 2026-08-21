import json, re
from collections import Counter
js = open(r'P:\LandingPage-PromptHub\js\prompts_library.js', encoding='utf-8').read()
data = json.loads(re.sub(r'^window.PROMPTS_LIBRARY = ', '', js).rstrip().rstrip(';'))

nums = [5,16,21,30,72,202,201,200,199,208,210,212,213,215,216,219,222,224,235,237,239,263]

# indices 1-based -> remover por posicao (ordem original, sem filtro)
idx_set = set(n-1 for n in nums)
kept = [x for i, x in enumerate(data) if i not in idx_set]
removed_by_num = len(data) - len(kept)

# exclui categoria outros
final = [x for x in kept if x['categoria'] != 'outros']
removed_outros = len(kept) - len(final)

open(r'P:\LandingPage-PromptHub\js\prompts_library.js', 'w', encoding='utf-8').write('window.PROMPTS_LIBRARY = %s;' % json.dumps(final, ensure_ascii=False))

print('removidos por numero:', removed_by_num)
print('removidos categoria outros:', removed_outros)
print('final:', len(final))
print('categorias:', dict(Counter(x['categoria'] for x in final)))