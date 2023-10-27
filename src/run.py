"""
$ cd src/
$ python run.py
"""
import os

from bottle import Bottle, request, HTTPResponse


app = Bottle(__name__)


def lambda_proxy_integration_event(
        path: str, method: str, headers: dict, query: dict, body: str) -> dict:
    return {
        'httpMethod': method,
        'headers': headers,
        'queryStringParameters': query,
        'requestContext': {
            'resourcePath': path,
            'authorizer': {
                'claims': {
                    'cognito:username': '',
                    'custom:customer': '',
                    'custom:role': '',
                    'custom:tenants': ''
                }
            }
        },
        'body': body,
        'isBase64Encoded': False
    }


@app.route('<path:path>',
           method=['GET', 'POST', 'PATCH', 'DELETE', 'PUT', 'HEAD'])
def callback(path):
    from commons import LambdaContext
    from lambdas.modular_api_handler.handler import lambda_handler
    event = lambda_proxy_integration_event(
        path=request.path,
        method=request.method,
        headers=dict(request.headers),
        query=dict(request.query),
        body=request.body.read().decode()
    )
    response = lambda_handler(event, LambdaContext())
    return HTTPResponse(
        body=response.get('body'),
        status=response.get('statusCode'),
        headers=response.get('headers')
    )


def set_envs():
    with open('.env', 'r') as file:
        for line in file:
            name, value = line.strip().split('=')
            os.environ[name] = value


if __name__ == '__main__':
    set_envs()
    app.run(port=5000)
