from rest_framework.parsers import JSONParser, FileUploadParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import Http404, JsonResponse, HttpResponseForbidden, HttpResponse
from django.apps import apps
from django.utils.timezone import datetime
from django.core.paginator import Paginator
from django import forms


import csv, codecs
from dataparser.apps import ExcelParser
from .instance import get_main_service
from datetime import date



class ServiceJSONDataAPIView(APIView):
    """

    """

    # permission_classes = [IsAuthenticated]

    def post(self, request, name):
        data = request.data
        if name:
            try:
                app_name = data.get('app_name', 'service')
                _filter = data.get('filter', {})
                _columns = data.get('columns', {})
                _page = data.get('page', 1)
                _pagination = data.get('pagination', 100)
                
                Model = apps.get_model(app_label=app_name, model_name=name)
                q = Model.objects.filter(**_filter).values(*_columns).order_by('-id')

                if _pagination:
                    paginator = Paginator(q, _pagination)
                    _res = paginator.get_page(_page)
                else:
                    paginator = False
                    _res = q
                
                if _columns:
                    _result = []
                    for _ in _res:
                        _r = []
                        for _col in _columns:
                            _r.append(_[_col])
                        _result.append(_r)
                else:
                    _result = list(_res)

                return JsonResponse({
                    'datetime': datetime.today(),
                    'columns': _columns,
                    'result': _result,
                    'total_page': paginator.num_pages if paginator else 1,
                    'total_count': paginator.count if paginator else q.count(),
                })
                
            except Exception as err:
                return HttpResponseForbidden(str(err))
        else:
            return JsonResponse({'name': 'none'}, safe=False)
        
        

class ServiceUploadAPIView(APIView):
    """
    """

    parser_classes = [MultiPartParser]
    # permission_classes = [IsAuthenticated]


    def post(self, request, name):
        data = request.data
        if name:
            try:
                _data = []

                if name == 'textbookuploadexcel':
                    _file = request.FILES['file']

                    _ep = ExcelParser(file_content=_file.read())
                    
                    _data = _ep.get_row_list(column=['发言内容', '状态', '權重'])

                    _done = get_main_service(is_admin=True).add_textbook_sentense(_data)

                    if not _done:
                        return JsonResponse({'error': 'Failed.', 'data': _data}, safe=False)

                return JsonResponse({
                    'name': name,
                    'datetime': datetime.today(),
                    'data': _data,
                })
                
            except Exception as err:
                return HttpResponseForbidden(str(err))
        else:
            return JsonResponse({'name': 'none'}, safe=False)


class ServiceRemoveAPIView(APIView):
    """
    """
    # permission_classes = [IsAuthenticated]

    def delete(self, request, name, id):
        data = request.data
        if name:
            try:
                if name == 'textbookremove':

                    _done = get_main_service(is_admin=True).remove_textbook_sentense(id)

                    if not _done:
                        return HttpResponseForbidden('Delete Failed.')

                return JsonResponse({
                    'id': id,
                    'datetime': datetime.today(),
                })
                
            except Exception as err:
                return HttpResponseForbidden(str(err))
        else:

            return JsonResponse({'name': 'none'}, safe=False)


class ServicePinyinBlockListAPIView(APIView):
    """
    """
    model = apps.get_model(app_label='service', model_name='DynamicPinyinBlock')

    def get(self, request, id):
        if id == 'list':
            today = date.today()
            _date = today.strftime("%Y%m%d")
            filename = '{}_block_list.csv'.format(_date)
            reslist = get_main_service(is_admin=True).get_dynamic_pinyin_block_list()
            
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = "attachment; filename=" + filename
            response.write(codecs.BOM_UTF8)
            writer = csv.writer(response)
            # writer.writeheader()
            for r in reslist:
                writer.writerow(r)
            return response
        
        return HttpResponseForbidden('Add Failed.')

    def post(self, request, id):
        result = []
        if id == 'add':
            texts = request.data.getlist('text[]')
            if texts:
                result = get_main_service(is_admin=True).add_pinyin_block(texts)
                print('result: ', result)

            return JsonResponse({'result': result}, safe=False)
        
        elif id == 'file':
            pass
        
        return HttpResponseForbidden('Add Failed.')
        

    def delete(self, request, id):
        try:
            id = int(id)
            if id > 0:

                _done = get_main_service(is_admin=True).remove_pinyin_block(id)

                if not _done:
                    return HttpResponseForbidden('Delete Failed.')

            return JsonResponse({
                'id': id,
                'datetime': datetime.today(),
            })
            
        except Exception as err:
            return HttpResponseForbidden(str(err))
