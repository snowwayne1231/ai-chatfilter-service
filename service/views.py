from rest_framework.parsers import JSONParser, FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView

class ServiceAPIView(APIView):
    """

    """

    parser_classes = [JSONParser, FileUploadParser]

    def post(self, request, format=None):
        file_obj = request.data['file']
        print('file_obj')
        print(file_obj)
        
        return Response({'recv': 'qq'})