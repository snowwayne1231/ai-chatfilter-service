from django.core.management.base import BaseCommand
from tcpsocket.main import LaunchTcpSocket 


class Command(BaseCommand):
    help = 'open tpc socket.'


    def add_arguments(self, parser):
        parser.add_argument(
            '-port', dest='port', required=False, help='port',
        )
        parser.add_argument(
            '-host', dest='host', required=False, help='host',
        )
        parser.add_argument(
            '-webport', dest='webport', required=False, help='webport',
        )
        parser.add_argument(
            '-webhost', dest='webhost', required=False, help='webhost',
        )


    def handle(self, *args, **options):
        port = options.get('port')
        host = options.get('host')
        webport = options.get('webport')
        webhost = options.get('webhost')
        
        if port is None:
            port = 8025
        else:
            port = int(port)
        
        if host is None:
            host = '0.0.0.0'
        
        if webport is None:
            webport = 8000
        else:
            webport = int(webport)

        if webhost is None:
            webhost = '127.0.0.1'
        # bufsize = 1024

        main = LaunchTcpSocket(host, port, webhost, webport)

