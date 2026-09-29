import os
import argparse
import json

def write_file(path: str, content: str = None, from_file: str = None, mode: str = 'w') -> dict:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        final_content = content
        if from_file and os.path.exists(from_file):
            with open(from_file, 'r', encoding='utf-8', errors='ignore') as f:
                final_content = f.read()
            if 'scratch' in from_file:
                try:
                    os.remove(from_file)
                except Exception:
                    pass

        with open(path, mode, encoding='utf-8') as f:
            f.write(final_content or '')

        return {'status': 'success', 'path': path, 'mode': mode}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True)
    parser.add_argument('--content', default=None)
    parser.add_argument('--from-file', default=None)
    parser.add_argument('--mode', default='w', choices=['w', 'a'])
    args = parser.parse_args()

    print(json.dumps(write_file(args.path, args.content, args.from_file, args.mode), indent=2))
