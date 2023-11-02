import json

from commons.constants import PARAM_MESSAGE


class ApplicationException(Exception):

    def __init__(self, code, content):
        self.code = code
        self.content = content

    def __str__(self):
        return f'{self.code}:{self.content}'

    def __repr__(self):
        return self.__str__()

    def response(self):
        return {
            'statusCode': self.code,
            'headers': {
                'Content-Type': 'application/json',
                'x-amzn-ErrorType': self.code,
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'isBase64Encoded': False,
            'body': json.dumps({
                PARAM_MESSAGE: self.content,
            })
        }
