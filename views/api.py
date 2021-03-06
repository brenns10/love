# -*- coding: utf-8 -*-
from flask import make_response
from flask import request

from errors import TaintedLove
from logic.love import get_love
from logic.love import send_loves
from main import app
from models import Employee
from util.decorators import api_key_required
from util.recipient import sanitize_recipients
from util.render import make_json_response
from views import common


LOVE_CREATED_STATUS_CODE = 201  # Created
LOVE_FAILED_STATUS_CODE = 418  # I'm a Teapot
LOVE_BAD_PARAMS_STATUS_CODE = 422  # Unprocessable Entity
LOVE_NOT_FOUND_STATUS_CODE = 404  # Not Found


# GET /api/love
@app.route('/api/love', methods=['GET'])
@api_key_required
def api_get_love():
    sender = request.args.get('sender')
    recipient = request.args.get('recipient')

    limit = request.args.get('limit')
    if limit:
        try:
            limit = int(limit)
        except ValueError:
            return make_response(
                'Invalid value for "limit": {0!r}'.format(limit),
                LOVE_BAD_PARAMS_STATUS_CODE)

    if not (sender or recipient):
        return make_response(
            'You must provide either a sender or a recipient.',
            LOVE_BAD_PARAMS_STATUS_CODE)

    love_found = get_love(
        sender_username=sender,
        recipient_username=recipient,
        limit=limit,
    ).get_result()

    return make_json_response([
        {
            'sender': Employee.key_to_username(love.sender_key),
            'recipient': Employee.key_to_username(love.recipient_key),
            'message': love.message,
            'timestamp': love.timestamp.isoformat(),
        }
        for love in love_found
    ])


# POST /api/love
@app.route('/api/love', methods=['POST'])
@api_key_required
def api_send_loves():
    sender = request.form.get('sender')
    recipients = sanitize_recipients(request.form.get('recipient'))
    message = request.form.get('message')

    try:
        recipients = send_loves(recipients, message, sender_username=sender)
        recipients_display_str = ', '.join(recipients)
        return make_response(
            u'Love sent to {}!'.format(recipients_display_str),
            LOVE_CREATED_STATUS_CODE,
            {}
        )
    except TaintedLove as exc:
        return make_response(
            exc.user_message,
            LOVE_FAILED_STATUS_CODE if exc.is_error else LOVE_CREATED_STATUS_CODE,
            {}
        )


@app.route('/api/autocomplete', methods=['GET'])
@api_key_required
def autocomplete():
    return common.autocomplete(request)
