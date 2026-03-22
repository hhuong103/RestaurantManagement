import google.generativeai as genai
print('version', getattr(genai, '__version__', None))
print('members:', [n for n in dir(genai) if not n.startswith('_')])
