from dotenv import load_dotenv
import os

class EnvVarsLoader:
    @staticmethod
    def load_env_vars():
        # Load .env from the project root (one directory up from this file)
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
        load_dotenv(dotenv_path=env_path)
        # Return a dictionary of all env vars loaded (filter for those in the .env file)
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, _ = line.split('=', 1)
                        key = key.strip()
                        value = os.environ.get(key)
                        if value is not None:
                            env_vars[key] = value
        return env_vars
