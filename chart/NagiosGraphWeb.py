from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    return "Status"

@app.route('/graph')
def status():
    return render_template('chart.html')

@app.route('/_add_numbers')
def add_numbers():
    a = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)
    print str(jsonify(result=a + b))
    return jsonify(result=a + b)

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int("8090"),
        debug=True
    )


