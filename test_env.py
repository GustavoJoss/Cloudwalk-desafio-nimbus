from pathlib import Path
import os
from dotenv import load_dotenv, dotenv_values

root = Path('.').resolve()
env_path = root / '.env'
print('cwd =', root)
print('env exists =', env_path.exists(), '| path =', env_path)

print('\n>> dotenv_values preview:')
print(dict(dotenv_values(env_path)))

load_dotenv(env_path)
print('\n>> os.getenv check:')
print('OPENAI_API_KEY present?', bool(os.getenv('OPENAI_API_KEY')))
if os.getenv('OPENAI_API_KEY'):
    print('prefix:', os.getenv('OPENAI_API_KEY')[:8])
