#!/usr/bin/env python
# -*- coding: utf-8 -*-


from telegram.ext import CommandHandler, Updater

import configparser

config = configparser.RawConfigParser()
config.read('rail.cfg')
token = config.get('telegram', 'token')

updater = Updater(token)


class MyCommandHandler(CommandHandler):
    def __init__(self, func, **kwargs):
        super(CommandHandler, self).__init__(
            func.__name__,
            func,
            **kwargs
            )


def command_maker(dispatcher):
    def command(**kwargs):
        def decorator(func):
            dispatcher.add_handler(
                MyCommandHandler(func, **kwargs)
                )
            return func
        return decorator
    return command


command = command_maker(updater.dispatcher)


@command()
def help(bot, update):
    update.message.reply_text("this is a helpful message")


@command(pass_arguments=True)
def date(bot, update, args):
    update.message.reply_text(
        "this command has arguments: {}".format(
            ', '.join(args)
            )
        )


if __name__ == '__main__':
    updater.start_polling()
    updater.idle()

# EOF
