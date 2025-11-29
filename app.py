from flask import Flask, render_template, request, jsonify
import subprocess, tempfile, os, sys, pathlib, resource

app = Flask(__name__, template_folder='templates')
THIS_DIR = pathlib.Path(__file__).parent.resolve()
INTERPRETER = str(THIS_DIR / "interpreter.py")

def _limit_resources():
    resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, resource.RLIM_INFINITY))
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_code():
    code = request.form.get('code', '')
    if not code.strip():
        return jsonify({'stdout': '', 'stderr': 'No code provided'}), 400

    with tempfile.NamedTemporaryFile(mode='w', suffix='.blg', delete=False, encoding='utf-8') as f:
        fname = f.name
        f.write(code)
    try:
        cmd = [sys.executable, INTERPRETER, fname]
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  encoding='utf-8', timeout=3, preexec_fn=_limit_resources)
        except TypeError:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  encoding='utf-8', timeout=3)
        except subprocess.TimeoutExpired:
            return jsonify({'stdout': '', 'stderr': 'Execution timed out.'})
        return jsonify({'stdout': proc.stdout, 'stderr': proc.stderr})
    finally:
        try:
            os.unlink(fname)
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True)
