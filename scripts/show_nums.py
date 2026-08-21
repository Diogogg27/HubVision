import json, re
js = open(r'P:\LandingPage-PromptHub\js\prompts_library.js', encoding='utf-8').read()
data = json.loads(re.sub(r'^window.PROMPTS_LIBRARY = ', '', js).rstrip().rstrip(';'))
nums = [5,16,21,30,72,202,201,200,199,208,210,212,213,215,216,219,222,224,235,237,239,263]
for n in nums:
    x = data[n-1]
    cat = x['categoria']
    pr = x['prompt'][:90].replace('\n', ' ')
    print('%d: [%s] %s' % (n, cat, pr))