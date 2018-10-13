#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple bot to get trains statuses.

Attempt to create a simple decorator that
explicitly marks commands to serve.

TODO: make the help command able to discover
others automatically
"""

import configparser
import json
import urllib3

from datetime import datetime

from telegram.ext import CommandHandler, Updater

config = configparser.RawConfigParser()
config.read('rail.cfg')
token = config.get('telegram', 'token')
api_key = config.get('railwayAPI', 'key')
api = 'https://api.railwayapi.com/v2'
updater = Updater(token)


def request(method, path):
    """Method to request data from the API"""
    url = api + path + '/apikey/' + api_key
    http = urllib3.PoolManager()
    response = http.request(method.upper(), url)
    data = json.loads(response.data.decode('utf-8'))
    http_response_code = data['response_code']
    if http_response_code == 200:
        return data
    else:
        return False  # TODO: specialise result according to documentation


def command_maker(dispatcher):
    """dispatcher is a telegram.ext.Updater.dispatcher object"""
    def command(**kwargs):
        def decorator(func):
            dispatcher.add_handler(
                CommandHandler(func.__name__, func, **kwargs)
                )
            return func
        return decorator
    return command


command = command_maker(updater.dispatcher)


@command()
def help(bot, update):
    message = "This is a not so helpful message"
    update.message.reply_text(message)


@command(pass_args=True)
def pnr(bot, update, args):
    pass


@command(pass_args=True)
def trains(bot, update, args):
    """Get a list of available trains between 2 stations today.
    Usage example: /trains awy sbc
    """
    try:
        departure, arrival = args
    except ValueError as exc:
        message = "Please provide exact departure and arrival stations"
    else:
        message = "Trains between {departure} and {arrival} are:\n{trains}"
        # querying API to get trains
        current_date = datetime.today().strftime('%d-%m-%Y')
        path = '/between/source/{departure}/dest/{arrival}/date/{date}'.format(
            departure=departure,
            arrival=arrival,
            date=current_date
            )
        data = request('GET', path)
        if not data:
            message = (
                "Unable to find trains. Please verify you entered "
                "the right code for each station"
                )
        else:
            trains = '\n'.join(
                [
                    '{name} (#{number}) D: {departure} A: {arrival}'.format(
                        name=train_infos['name'],
                        number=train_infos['number'],
                        departure=train_infos['src_departure_time'],
                        arrival=train_infos['dest_arrival_time']
                        )
                    for train_infos in data['trains']
                    ]
                )
            message = message.format(
                departure=departure,
                arrival=arrival,
                trains=trains
                )
    finally:
        update.message.reply_text(message)


@command(pass_args=True)
def live(bot, update, args):
    """Gives the live position of a train.
    Required args are the train number and the date.
    Usage example: /live 12046 01-12-2018
    """
    try:
        train_number, date = args
    except ValueError as exc:
        message = (
            "Please provide the train number and the date. "
            "Date format is dd-mm-yyyy"
            )
    else:
        path = '/live/train/{train}/date/{date}'.format(
            train=train_number,
            date=date
            )
        data = request('GET', path)
        if not data:
            message = "Couldn't retrieve live position"
        else:
            train_name = data['train']['name']
            position = data['position']
            message = (
                'Train: {name}\n'
                'Status: {position}'
                ).format(
                    name=train_name,
                    position=position
                    )
    finally:
        update.message.reply_text(message)


@command(pass_args=True)
def arrivals(bot, update, args):
    """Returns a list of trains arriving at a given station
    within a window period (bonus: live position is displayed)
    Usage example: /arrivals sbc 2
    """
    try:
        station_code, hours_window = args
    except ValueError as exc:
        message = "Please provide exact station code and hours window"
    else:
        # for now we won't implement a date validator
        path = '/arrivals/station/{station}/hours/{hours}'.format(
            station=station_code,
            hours=hours_window
            )
        data = request('GET', path)
        if not data:
            message = "Something went horribly wrong :-/"
        else:
            arriving_trains = data['trains']
            total_trains = data['total']
            window_text = hours_window + ' hours'
            if hours_window == 1:
                window_text = 'hour'
            if arriving_trains:
                message = (
                    '{total} trains arriving '
                    'in the next {window_text}'.format(
                        total=total_trains,
                        window_text=window_text
                        )
                    )
                for arriving_train in arriving_trains:
                    train_name = arriving_train["name"]
                    train_number = arriving_train["number"]

                    sch_arr = arriving_train["scharr"]
                    act_arr = arriving_train["actarr"]
                    delay_arr = arriving_train["delayarr"]

                    sched_dep = arriving_train["schdep"]
                    act_dep = arriving_train["actdep"]
                    delay_dep = arriving_train["delaydep"]

                    msg = (
                        'Train: {name}\n'
                        'Train Number: {number}\n'
                        'Scheduled Arrival: {scharr}\n'
                        'Actual Arrival: {actarr}\n'
                        'Delay in Arrival: {delayarr}\n'
                        'Scheduled Departure: {schdep}\n'
                        'Actual Departure: {actdep}\n'
                        'Delay in Departure: {delaydep}'
                        ).format(
                            name=train_name,
                            number=train_number,
                            scharr=sch_arr,
                            actarr=act_arr,
                            delayarr=delay_arr,
                            schdep=sched_dep,
                            actdep=act_dep,
                            delaydep=delay_dep
                            )
                    message += '\n{}'.format(msg)
            else:
                message = "No arriving trains in the next {window_text}".format(
                    window_text=window_text
                    )
    finally:
        update.message.reply_text(message)


if __name__ == '__main__':
    updater.start_polling()
    updater.idle()

# EOF
