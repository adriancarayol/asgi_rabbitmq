import atexit
import statistics
import time
from collections import defaultdict
from operator import itemgetter

from pika import SelectConnection
from pika.channel import Channel
from pika.connection import LOGGER
from tabulate import tabulate

stats = defaultdict(list)


def print_stats():

    headers = ['method', 'calls', 'mean', 'median', 'stdev']
    data = []
    for method, latencies in stats.items():
        data.append([
            method,
            len(latencies),
            statistics.mean(latencies),
            statistics.median(latencies),
            statistics.stdev(latencies) if len(latencies) > 1 else None,
        ])
    data = sorted(data, key=itemgetter(1), reverse=True)
    print(tabulate(data, headers))


atexit.register(print_stats)


class DebugConnection(SelectConnection):
    """Collect statistics about RabbitMQ methods usage on connection."""

    def _create_channel(self, channel_number, on_open_callback):

        LOGGER.debug('Creating channel %s', channel_number)
        return DebugChannel(self, channel_number, on_open_callback)


class DebugChannel(Channel):
    """Collect statistics about RabbitMQ methods usage on channel."""

    def basic_ack(self, *args, **kwargs):
        return super(DebugChannel, self).basic_ack(*args, **kwargs)

    def basic_cancel(self, *args, **kwargs):
        return super(DebugChannel, self).basic_cancel(*args, **kwargs)

    def basic_consume(self, *args, **kwargs):
        return super(DebugChannel, self).basic_consume(*args, **kwargs)

    def basic_publish(self, *args, **kwargs):
        return super(DebugChannel, self).basic_publish(*args, **kwargs)

    def exchange_bind(self,
                      callback=None,
                      destination=None,
                      source=None,
                      routing_key='',
                      nowait=False,
                      arguments=None):
        start = time.time()

        def callback_wrapper(method_frame):
            latency = time.time() - start
            stats['exchange_bind'].append(latency)
            if callback:
                callback(method_frame)

        return super(DebugChannel, self).exchange_bind(
            callback_wrapper, destination, source, routing_key, nowait,
            arguments)

    def exchange_declare(self,
                         callback=None,
                         exchange=None,
                         exchange_type='direct',
                         passive=False,
                         durable=False,
                         auto_delete=False,
                         internal=False,
                         nowait=False,
                         arguments=None,
                         type=None):
        start = time.time()

        def callback_wrapper(method_frame):
            latency = time.time() - start
            stats['exchange_declare'].append(latency)
            if callback:
                callback(method_frame)

        return super(DebugChannel, self).exchange_declare(
            callback_wrapper, exchange, exchange_type, passive, durable,
            auto_delete, internal, nowait, arguments, type)

    def exchange_delete(self,
                        callback=None,
                        exchange=None,
                        if_unused=False,
                        nowait=False):
        start = time.time()

        def callback_wrapper(method_frame):
            latency = time.time() - start
            stats['exchange_delete'].append(latency)
            if callback:
                callback(method_frame)

        return super(DebugChannel, self).exchange_delete(
            callback_wrapper, exchange, if_unused, nowait)

    def exchange_unbind(self, *args, **kwargs):
        return super(DebugChannel, self).exchange_unbind(*args, **kwargs)

    def queue_bind(self,
                   callback,
                   queue,
                   exchange,
                   routing_key=None,
                   nowait=False,
                   arguments=None):
        start = time.time()

        def callback_wrapper(method_frame):
            latency = time.time() - start
            stats['queue_bind'].append(latency)
            callback(method_frame)

        return super(DebugChannel, self).queue_bind(
            callback_wrapper, queue, exchange, routing_key, nowait, arguments)

    def queue_declare(self,
                      callback,
                      queue='',
                      passive=False,
                      durable=False,
                      exclusive=False,
                      auto_delete=False,
                      nowait=False,
                      arguments=None):
        start = time.time()

        def callback_wrapper(method_frame):
            latency = time.time() - start
            stats['queue_declare'].append(latency)
            callback(method_frame)

        return super(DebugChannel, self).queue_declare(
            callback_wrapper, queue, passive, durable, exclusive, auto_delete,
            nowait, arguments)
