from rest_framework.parsers import JSONParser, FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404, JsonResponse
from django.apps import apps
from django.utils.timezone import datetime

class ServiceAPIView(APIView):
    """

    """

    parser_classes = [JSONParser, FileUploadParser]

    def post(self, request, format=None):
        file_obj = request.data['file']
        
        return Response({'recv_file': file_obj})



class ServiceJSONDataAPIView(APIView):
    """

    """

    def post(self, request, name):
        data = request.data
        if name:
            try:
                app_name = data.get('app_name', 'service')
                _filter = data.get('filter', {})
                _columns = data.get('columns', {})
                Model = apps.get_model(app_label=app_name, model_name=name)
                q = Model.objects.filter(**_filter).values(*_columns)
                
                if _columns:
                    _result = []
                    for _ in q:
                        _r = []
                        for _col in _columns:
                            _r.append(_[_col])
                        _result.append(_r)
                else:
                    _result = list(q)

                return JsonResponse({
                    'datetime': datetime.today(),
                    'columns': _columns,
                    'result': _result,
                })
                
            except Exception as err:
                return JsonResponse({'error': str(err)}, safe=False)
        else:
            return JsonResponse({'name': 'none'}, safe=False)
        
        
    