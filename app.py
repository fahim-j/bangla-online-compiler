# app.py
# Run: pip install -r requirements.txt
#      python3 app.py
# Open http://127.0.0.1:5000

from flask import Flask, render_template, request, jsonify
import subprocess, tempfile, os, sys, shlex
import resource    # unix-only; used to limit resources for safety
import signal
import pathlib

app = Flask(__name__, template_folder='templates')

# Path to the interpreter script bundled below
THIS_DIR = pathlib.Path(__file__).parent.resolve()
INTERPRETER = str(THIS_DIR / "interpreter.py")

# helper: preexec to set resource limits (only on Unix)
def _limit_resources():
    # 100 MB address space
    resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, resource.RLIM_INFINITY))
    # limit CPU time to 2 seconds
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_code():
    code = request.form.get('code', '')
    if not code.strip():
        return jsonify({'stdout': '', 'stderr': 'No code provided'}), 400

    # write code to a temporary file (UTF-8)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.blg', delete=False, encoding='utf-8') as f:
        fname = f.name
        f.write(code)
    try:
        # call the interpreter as a subprocess with resource limits and timeout
        # Using "python3 interpreter.py <file>"
        cmd = [sys.executable, INTERPRETER, fname]
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                timeout=3,
                preexec_fn=_limit_resources  # unix only; on Windows this will error — optional
            )
            stdout = proc.stdout
            stderr = proc.stderr
        except TypeError:
            # If preexec_fn not supported (windows), run without it
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                timeout=3
            )
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired:
            stdout = ''
            stderr = 'Error: execution timed out.'
        return jsonify({'stdout': stdout, 'stderr': stderr})
    finally:
        try:
            os.unlink(fname)
        except:
            pass

if __name__ == '__main__':
    # For development only. Use gunicorn/nginx for production.
    app.run(debug=True)
